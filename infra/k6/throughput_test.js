import { Kafka } from "k6/x/kafka";
import { sleep } from "k6";

// k6 Kafka throughput test: simulate 50K Redpanda events/day
// 50,000 / 86,400 seconds ≈ 0.578 messages/second sustained

export const options = {
  scenarios: {
    kafka_throughput: {
      executor: "constant-arrival-rate",
      rate: 1,                  // 1 message/sec sustained
      timeUnit: "1s",
      duration: "5m",           // 5 min test = 300 msgs (scale up for full day sim)
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
  },
  thresholds: {
    kafka_writer_error_count: ["count<10"],  // Less than 10 produce errors
  },
};

const kafka = new Kafka({
  brokers: [__ENV.KAFKA_BROKERS || "localhost:9092"],
});

const writer = kafka.writer({ topic: "dependency.resolved" });

export default function () {
  const msg = {
    key: `CVE-LOAD-${Math.floor(Math.random() * 10000)}`,
    value: JSON.stringify({
      cve_id: `CVE-LOAD-${Math.floor(Math.random() * 10000)}`,
      root_package: "test-package",
      ecosystem: ["npm", "pypi", "maven"][Math.floor(Math.random() * 3)],
      cvss_score: 5 + Math.random() * 5,
      blast_radius_size: Math.floor(Math.random() * 500),
    }),
  };

  writer.produce({ messages: [msg] });
}

export function teardown() {
  writer.close();
  kafka.close();
}
