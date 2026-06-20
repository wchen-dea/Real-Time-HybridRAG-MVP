package com.dataops.hybridrag.flink;

import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class EmbeddingUDFTest {

    private MockWebServer mockServer;
    private EmbeddingUDF udf;

    @BeforeEach
    void setUp() throws Exception {
        mockServer = new MockWebServer();
        mockServer.start();

        // Use the package-private constructor to inject the mock server URL directly,
        // avoiding any need to manipulate real environment variables.
        String invocationsUrl = mockServer.url("/serving-endpoints/test-embed-model/invocations").toString();
        udf = new EmbeddingUDF(invocationsUrl, "test-token");
        udf.open(null);
    }

    @AfterEach
    void tearDown() throws Exception {
        mockServer.shutdown();
    }

    @Test
    void eval_returnsEmbeddingOnSuccessResponse() throws Exception {
        mockServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {
                          "data": [{"embedding": [0.1, 0.2, 0.3], "index": 0, "object": "embedding"}],
                          "model": "test-embed-model",
                          "object": "list"
                        }
                        """));

        Float[] result = udf.eval("Kafka lag handling runbook");

        assertEquals(3, result.length);
        assertEquals(0.1f, result[0], 1e-5f);
        assertEquals(0.2f, result[1], 1e-5f);
        assertEquals(0.3f, result[2], 1e-5f);
    }

    @Test
    void eval_sendsCorrectRequestBody() throws Exception {
        mockServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {"data": [{"embedding": [0.5], "index": 0, "object": "embedding"}]}
                        """));

        udf.eval("test chunk");

        RecordedRequest req = mockServer.takeRequest();
        assertEquals("POST", req.getMethod());
        String body = req.getBody().readUtf8();
        assertTrue(body.contains("\"input\""), "Request body must contain 'input' field");
        assertTrue(body.contains("test chunk"), "Request body must contain the chunk text");
        assertEquals("Bearer test-token", req.getHeader("Authorization"));
    }

    @Test
    void eval_returnsEmptyArrayOnHttpError() throws Exception {
        mockServer.enqueue(new MockResponse().setResponseCode(429).setBody("rate limited"));

        Float[] result = udf.eval("some text");

        assertNotNull(result);
        assertEquals(0, result.length);
    }

    @Test
    void eval_returnsEmptyArrayForNullInput() throws Exception {
        Float[] result = udf.eval(null);
        assertNotNull(result);
        assertEquals(0, result.length);
    }

    @Test
    void eval_returnsEmptyArrayForBlankInput() throws Exception {
        Float[] result = udf.eval("   ");
        assertNotNull(result);
        assertEquals(0, result.length);
    }

    @Test
    void eval_returnsEmptyArrayOnMalformedResponse() throws Exception {
        mockServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"unexpected\": true}"));

        Float[] result = udf.eval("some text");

        assertNotNull(result);
        assertEquals(0, result.length);
    }

    @Test
    void parseEmbedding_parsesLargeVector() throws Exception {
        StringBuilder sb = new StringBuilder("{\"data\": [{\"embedding\": [");
        for (int i = 0; i < 1024; i++) {
            if (i > 0) sb.append(",");
            sb.append(i * 0.001);
        }
        sb.append("], \"index\": 0, \"object\": \"embedding\"}]}");

        Float[] result = udf.parseEmbedding(sb.toString());
        assertEquals(1024, result.length);
        assertEquals(0f, result[0], 1e-5f);
        assertEquals(0.001f, result[1], 1e-4f);
    }
}

