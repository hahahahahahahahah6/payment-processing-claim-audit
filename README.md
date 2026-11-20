# Documentation claim auditor

This offline static checker compares documentation statements about the checked capability with recognizable Python call sites. It scans the root README and Markdown below a docs directory, excluding fenced blocks; inline code counts. It parses source without executing it and excludes examples, fixtures, documentation, and symbolic links. Test evidence is reported separately. Exact phrases and listed denials determine matching; review findings in context.

```sh
payment-processing-claim-audit audit . --json
payment-processing-claim-audit audit . --fail-on medium --ignore vendor/
python3 -m payment_processing_claim_audit --version
```

Findings use these identifiers:

```text
documented-payment-processing-claim-false
documented-no-payment-processing-claim-false
```

A missing production operation is high severity, or medium when found only in tests. A denial contradicted by production code is high severity. The default threshold is high; exit status 0 means the threshold was not met, 2 means it was met, and 1 indicates a usage or I/O error. JSON includes a verdict, findings, and messages. Verbose mode adds details. Ignore prefixes may be repeated.

## Differentiation

The checker recognizes typed calls, selected service chains, and paired construction and operation calls for major providers, as well as specific generic names. A generic HTTP request to a provider host with a string path is API request evidence but does not establish the checked operation. A typed call and a generic request can satisfy both audits. Their claim wording differs. Uploads and downloads concern files; web scraping reads pages. A fetch alone is insufficient. Database auditing checks connections and queries; its claim wording also differs.

Document extraction reads fields, while the checked operation concerns a customer transaction. Invoice generation creates a bill. Authentication, encryption, subscription management, payouts, transfers, card tokenisation, webhooks, caching, and text or document generation each concern different capabilities and wording. These claims do not trigger this checker. A provider SDK call using a key or TLS is not itself authentication or encryption evidence. Importable API surface auditing checks names and arguments, not the checked capability. Offline, privacy, timeout and server-sent event checks use transport calls for different questions. Provider mentions and configuration alone are not claims of the checked capability.

## Limitations

Exact wording can describe a configuration page, deployment instructions, a hosted button, or card validation rather than an operation in this repository. Review findings in context. Session creation counts even in setup mode, which only saves a card. Some order creation calls establish an order but the customer must still pay, and capture may be required. A request construction paired with execute may execute a different object. A call site can be dead code, behind a flag, or use a test key; all count. A client alone or an unpaired operation in a paired route is insufficient, and each pair must appear in one module.

Generic HTTP requests, webhook handlers, subscription, invoice and customer creation, tokenisation, outgoing transfers, and subprocess commands are excluded. Transaction cloning and donations are not traced. Document extraction calls from Mindee, Azure Document Intelligence, Veryfi, Google Document AI, Eden AI, Textract, LlamaParse, Nanonets, Docsumo, ABBYY Vantage, Rossum, Klippa, Parseur and Extend are excluded: they read documents or use opaque identifiers, not fixed fingerprints for the checked capability. Static patterns are not semantic judgment; unresolved aliases and invalid Python are missed. Only listed exact phrases and denials count.
