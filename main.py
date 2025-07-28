from quart import Quart, request, render_template, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import asyncio
import json
import uuid
import os

load_dotenv()

app = Quart(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = AsyncOpenAI()

class InvalidModelResponseError(Exception):
    pass

class DataFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self._df = pd.read_excel(filepath)
        self._df.columns = self._df.columns.str.strip().str.lower()

        for col in ["phone number", "phone number source", "email address", "email address source"]:
            if col not in self._df.columns:
                self._df[col] = pd.Series(dtype="object")
            else:
                self._df[col] = self._df[col].astype("object")

    def get_company_names(self):
        return self._df["company name"].dropna().unique()

    @staticmethod
    def is_blank(value):
        return pd.isna(value) or str(value).strip() == ""

    def save(self, data, force_update=False):
        logs = []
        for c_name, info in data.items():
            row_idx = self._df.loc[self._df["company name"] == c_name].index
            if not row_idx.empty:
                idx = row_idx[0]
                log = {"company name": c_name}

                if force_update or self.is_blank(self._df.at[idx, "phone number"]):
                    self._df.at[idx, "phone number"] = info.get("phone", "")
                    self._df.at[idx, "phone number source"] = info.get("phone_source", "")

                if force_update or self.is_blank(self._df.at[idx, "email address"]):
                    self._df.at[idx, "email address"] = info.get("email", "")
                    self._df.at[idx, "email address source"] = info.get("email_source", "")

                log["email"] = self._df.at[idx, "email address"]
                log["phone"] = self._df.at[idx, "phone number"]
                logs.append(log)

        self._df.to_excel(self.filepath, index=False)

        log_df = pd.DataFrame(logs)
        log_name = os.path.basename(self.filepath).replace(".xlsx", "_log.csv")
        log_path = os.path.join(app.config['UPLOAD_FOLDER'], log_name)
        log_df.to_csv(log_path, index=False)
        return log_name

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/process', methods=['POST'])
async def process_ajax():
    files = await request.files
    form = await request.form

    file = files.get('file')
    raw_text = form.get('company_names', '').strip()
    force_update = form.get("force_update") == "on"
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if file:
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "Only .xlsx files are supported."}), 400

        filename = f"{timestamp}_{session_id}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        await file.save(filepath)
    elif raw_text:
        companies = [line.strip() for line in raw_text.split('\n') if line.strip()]
        filename = f"{timestamp}_{session_id}_from_text.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pd.DataFrame({'company name': companies}).to_excel(filepath, index=False)
    else:
        return jsonify({"error": "No input provided"}), 400

    # Process the file
    log_filename, statuses = await process_file_ajax(filepath, force_update)

    return jsonify({
        "message": "Processing complete",
        "file_url": url_for('download_file', filename=os.path.basename(filepath)),
        "log_url": url_for('download_file', filename=log_filename),
        "statuses": statuses
    })

@app.route("/download/<filename>")
async def download_file(filename):
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(full_path):
        return await send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    return "File not found", 404

async def process_file_ajax(filepath, force_update):
    df = DataFile(filepath)
    names = df.get_company_names()
    statuses = []
    results = []

    for name in names:
        result = await get_contact_info(name)
        results.append(result)
        statuses.append({
            "company": name,
            "status": "done" if result[1].get("email") or result[1].get("phone") else "empty"
        })

    company_data = {name: info for name, info in results}
    log_filename = df.save(company_data, force_update=force_update)
    return log_filename, statuses

async def get_contact_info(entity, retries=2):
    prompt = f"""
You are a helpful assistant.

I need official contact information for the following entity: {entity}

Please provide:
1. The most likely and relevant public **phone number** (e.g. for support/inquiries).
2. The most relevant public **email address**.
3. For each, include the best possible **source URL**.

Respond only in raw JSON format, no explanation, markdown, or code blocks.

Format:
{{
  "phone": "...",
  "phone_source": "https://...",
  "email": "...",
  "email_source": "https://..."
}}
"""
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            reply = response.choices[0].message.content
            return entity, json.loads(reply)
        except Exception as e:
            print(f"[Attempt {attempt + 1}] Failed for {entity}: {e}")
            await asyncio.sleep(1)

    return entity, {
        "phone": "",
        "phone_source": "",
        "email": "",
        "email_source": ""
    }

if __name__ == '__main__':
    asyncio.run(app.run_task(host="0.0.0.0", port=int(os.getenv("PORT", 5000))))