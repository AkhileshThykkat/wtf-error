# Finish the incident investigation workspace

These are the natural-language prompts for the requested implementation work, grouped by the pieces of the user-facing flow.

## Make pasted evidence safe and useful

> Can you add a place to save logs and command output on an incident? Please mask common secrets before anything gets stored or sent to the model, and label each line so a finding can point back to the exact evidence. Keep the original incident and findings data intact as the database grows.

## Connect the investigation to the whole incident

> I want to be able to ask a follow-up question and have the investigation see the incident, saved evidence, earlier chat, and previous findings together. Check the model response before saving it, keep the assistant reply in the conversation, and only save findings that cite real evidence line IDs. Use the Llama 3.3 Workers AI model from the architecture sketch.

## Give the workflow a usable web page

> Please make a small web interface where I can create an incident, read its symptoms, add evidence, ask questions, and review findings. It should work on a phone as well as a laptop, and make evidence citations easy to follow back to the log lines.

## Keep it on the existing Cloudflare Worker

> Serve the page and API from this project’s Worker, and configure the D1 and Workers AI bindings the code uses. Keep the change focused on the flow we already discussed; don’t add accounts, background jobs, or extra services.
