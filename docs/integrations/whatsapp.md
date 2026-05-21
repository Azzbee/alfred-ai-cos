# WhatsApp messaging

Albert can send a WhatsApp message through Meta's official **WhatsApp Business Cloud API**.
This is a level-3 (external communication) capability: it runs only after approval and
writes an audit row.

## What is built

- `app/capabilities/providers/whatsapp_message.py`: sends a message via the Cloud API
  `messages` endpoint. The only place the WhatsApp API is touched.
- Registers only when `WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` are set;
  otherwise `send_message` has no provider and is blocked with an audit row.
- Sends a **template** message by default. Inside a 24-hour customer-initiated session
  window, a free-form `body` is allowed.

## What is explicitly refused

Unofficial WhatsApp automation is not built and will not be:

- Driving WhatsApp Web / a personal account through a browser or unofficial library.
- Unsolicited bulk or proactive messaging to people who have not opted in.

Both violate Meta's terms and get phone numbers permanently banned. "WhatsApp automation"
as a general capability is not compliant; the official API with templates and opt-in
sessions is the only path, and that is what this provider uses.

## Sandbox reality

The Cloud API test setup only sends to **pre-verified recipient numbers** and only with
**approved message templates** outside the session window. So the sandbox proves the path
end to end without being able to message arbitrary people. That limitation is the point.

## Legal / compliance prerequisites (before production)

Your responsibility, not the code's:

1. A **Meta Business account** and a WhatsApp Business Account (WABA).
2. A **verified business** and a registered sender phone number.
3. **Approved message templates** for any out-of-session message.
4. **Opt-in**: recipients must have consented to be messaged by your business.
5. Adherence to Meta's **messaging policy** and rate limits.

## Configuration

```
WHATSAPP_ACCESS_TOKEN=...        # Cloud API access token
WHATSAPP_PHONE_NUMBER_ID=...     # the sender's phone number id
```

## Payload shape

A `send_message` proposal's `target`:

```json
{
  "to": "15551234567",
  "template": "appointment_reminder",
  "language": "en_US"
}
```

Or, within a session window:

```json
{ "to": "15551234567", "body": "Confirming our 2pm call tomorrow." }
```
