package com.dataops.hybridrag.flink;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.flink.table.functions.FunctionContext;
import org.apache.flink.table.functions.ScalarFunction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Flink scalar UDF: generate_embedding(STRING) -> ARRAY&lt;FLOAT&gt;
 *
 * <p>Calls the Databricks model serving endpoint configured via environment variables
 * to produce a dense embedding vector for each chunk_text value.
 *
 * <p>Required environment variables:
 * <ul>
 *   <li>DATABRICKS_HOST  – workspace URL, e.g. https://my-workspace.cloud.databricks.com</li>
 *   <li>DATABRICKS_TOKEN – personal access token or service principal token</li>
 * </ul>
 *
 * <p>Optional:
 * <ul>
 *   <li>AI_SEARCH_EMBEDDING_MODEL_ENDPOINT – model serving endpoint name
 *       (default: databricks-gte-large-en)</li>
 *   <li>EMBEDDING_CONNECT_TIMEOUT_MS  – HTTP connect timeout in ms (default: 10000)</li>
 *   <li>EMBEDDING_REQUEST_TIMEOUT_MS  – HTTP request timeout in ms (default: 30000)</li>
 * </ul>
 *
 * <p>Request shape (OpenAI-compatible):
 * <pre>POST /serving-endpoints/{model}/invocations
 * {"input": ["chunk text"]}</pre>
 *
 * <p>Expected response shape:
 * <pre>{"data": [{"embedding": [0.1, ...], "index": 0, "object": "embedding"}], ...}</pre>
 *
 * <p>Returns an empty Float[] on HTTP errors or parsing failures so the pipeline
 * continues; errors are logged at ERROR level for alerting.
 */
public class EmbeddingUDF extends ScalarFunction {

    private static final long serialVersionUID = 1L;

    private static final Logger LOG = LoggerFactory.getLogger(EmbeddingUDF.class);

    private static final String DEFAULT_MODEL_ENDPOINT = "databricks-gte-large-en";
    private static final int DEFAULT_CONNECT_TIMEOUT_MS = 10_000;
    private static final int DEFAULT_REQUEST_TIMEOUT_MS = 30_000;

    // Transient: not serialized across checkpoints; re-initialized in open()
    private transient HttpClient httpClient;
    private transient String endpointUrl;
    private transient String bearerToken;
    private transient ObjectMapper objectMapper;

    // Optional overrides injected at construction time (primarily for testing).
    // When null, open() falls back to environment variables.
    private final String endpointUrlOverride;
    private final String tokenOverride;

    /** Production constructor: reads all config from environment variables in open(). */
    public EmbeddingUDF() {
        this.endpointUrlOverride = null;
        this.tokenOverride = null;
    }

    /**
     * Test/override constructor: bypasses environment variable lookup.
     *
     * @param endpointUrl full invocations URL of the model serving endpoint
     * @param token       bearer token
     */
    EmbeddingUDF(String endpointUrl, String token) {
        this.endpointUrlOverride = endpointUrl;
        this.tokenOverride = token;
    }

    @Override
    public void open(FunctionContext context) throws Exception {
        if (endpointUrlOverride != null) {
            this.endpointUrl = endpointUrlOverride;
            this.bearerToken = tokenOverride;
        } else {
            String databricksHost = requireEnv("DATABRICKS_HOST").replaceAll("/+$", "");
            this.bearerToken = requireEnv("DATABRICKS_TOKEN");
            String modelEndpoint = envOrDefault("AI_SEARCH_EMBEDDING_MODEL_ENDPOINT", DEFAULT_MODEL_ENDPOINT);
            this.endpointUrl = databricksHost + "/serving-endpoints/" + modelEndpoint + "/invocations";
        }

        int connectMs = Integer.parseInt(envOrDefault("EMBEDDING_CONNECT_TIMEOUT_MS",
                String.valueOf(DEFAULT_CONNECT_TIMEOUT_MS)));

        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(connectMs))
                .build();
        this.objectMapper = new ObjectMapper();

        LOG.info("EmbeddingUDF initialized: endpoint={}", endpointUrl);
    }

    /**
     * Entry point invoked by Flink for each row.
     *
     * @param chunkText text to embed; null or blank returns an empty array
     * @return dense embedding vector as Float[], or empty Float[] on failure
     */
    public Float[] eval(String chunkText) {
        if (chunkText == null || chunkText.isBlank()) {
            return new Float[0];
        }
        try {
            String requestBody = buildRequestBody(chunkText);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(endpointUrl))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + bearerToken)
                    .timeout(Duration.ofMillis(DEFAULT_REQUEST_TIMEOUT_MS))
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                LOG.error("Embedding endpoint returned HTTP {} for text length {}: {}",
                        response.statusCode(), chunkText.length(), response.body());
                return new Float[0];
            }

            return parseEmbedding(response.body());

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.error("Embedding call interrupted for text length {}", chunkText.length());
            return new Float[0];
        } catch (Exception e) {
            LOG.error("Embedding call failed for text length {}: {}", chunkText.length(), e.getMessage(), e);
            return new Float[0];
        }
    }

    // -------------------------------------------------------------------------
    // Package-private helpers (also used by unit tests)
    // -------------------------------------------------------------------------

    String buildRequestBody(String chunkText) throws Exception {
        ObjectNode body = objectMapper.createObjectNode();
        ArrayNode inputs = body.putArray("input");
        inputs.add(chunkText);
        return objectMapper.writeValueAsString(body);
    }

    Float[] parseEmbedding(String responseBody) throws Exception {
        JsonNode root = objectMapper.readTree(responseBody);
        JsonNode embeddingNode = root.path("data").path(0).path("embedding");

        if (embeddingNode.isMissingNode() || !embeddingNode.isArray()) {
            LOG.warn("Unexpected embedding response shape (missing data[0].embedding)");
            return new Float[0];
        }

        Float[] embedding = new Float[embeddingNode.size()];
        for (int i = 0; i < embeddingNode.size(); i++) {
            embedding[i] = (float) embeddingNode.get(i).asDouble();
        }
        return embedding;
    }

    // -------------------------------------------------------------------------
    // Internal utilities
    // -------------------------------------------------------------------------

    private static String requireEnv(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(
                    "Required environment variable is not set: " + name);
        }
        return value;
    }

    private static String envOrDefault(String name, String defaultValue) {
        String value = System.getenv(name);
        return (value != null && !value.isBlank()) ? value : defaultValue;
    }
}
