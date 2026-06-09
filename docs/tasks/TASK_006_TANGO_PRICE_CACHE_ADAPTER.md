# TASK 006 - Tango price cache adapter

Owner: Tango + Atlas

Implement an adapter that converts Tango price list rows into PriceRecord objects.

Do not require live Tango access for tests. Use fixture JSON.

Acceptance:

- fixture -> PriceCache
- PriceCache can price an ERPNext quotation payload
- missing prices are reported clearly
