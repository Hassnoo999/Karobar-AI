// Run with Node 22: node --test tests/receipt-review.test.cjs
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { runInNewContext } = require("node:vm");
const test = require("node:test");
const assert = require("node:assert/strict");
const ts = require("typescript");
const output = ts.transpileModule(readFileSync(join(__dirname, "../lib/receipt-review.ts"), "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const helpers = { exports: {} };
runInNewContext(output, helpers);
const { receiptFileError, receiptMime, withTransferDirection } = helpers.exports;
const photo = { name: "receipt.png", type: "image/png", size: 1500 };

test("chooser and drop accept the same supported photo, including empty browser MIME", () => {
  assert.equal(receiptFileError([photo]), null);
  assert.equal(receiptFileError([{...photo, type: ""}]), null);
  assert.equal(receiptMime({...photo, type: ""}), "image/png");
});
test("reject empty, multiple, oversized and unsupported files before a request", () => {
  for (const files of [[], [photo, photo], [{...photo, size: 0}], [{...photo, size: 4 * 1024 * 1024 + 1}],
    [{...photo, name: "receipt.pdf", type: "application/pdf"}], [{...photo, name: "receipt.heic", type: ""}]]) {
    assert.equal(typeof receiptFileError(files), "string");
  }
});
test("receiving fills sender; sending fills recipient; neither invents business type", () => {
  const draft = {sender_name: "Sender", recipient_name: "Recipient", event_type: null, customer_name: null};
  const received = withTransferDirection(draft, "received");
  const sent = withTransferDirection(draft, "sent");
  assert.equal(received.customer_name, "Sender");
  assert.equal(sent.customer_name, "Recipient");
  assert.equal(received.event_type, null);
  assert.equal(sent.event_type, null);
  assert.equal(draft.customer_name, null);
});
test("changing direction clears contradictory type and stale linked customer", () => {
  const sent = withTransferDirection({sender_name: "Sender", recipient_name: "Recipient", event_type: "credit_received", customer_id: 7, payment_type: "credit"}, "sent");
  assert.equal(sent.event_type, null);
  assert.equal(sent.customer_id, null);
  assert.equal(sent.payment_type, null);
  assert.equal(withTransferDirection({event_type: "expense"}, "received").event_type, null);
});
test("missing other-party name remains editable, never fills merchant's own name", () => {
  assert.equal(withTransferDirection({recipient_name: "Merchant", event_type: null}, "received").customer_name, "");
});
