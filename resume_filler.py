from docx import Document
import os
import json

def fill_resume_template(data: dict, template_path='templates/resume_template.docx', output_folder='output') -> str:
    doc = Document(template_path)

    for paragraph in doc.paragraphs:
        inline_replacement(paragraph, data)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    inline_replacement(paragraph, data)

    os.makedirs(output_folder, exist_ok=True)
    file_name = f"resume_{data.get('full_name', 'user').replace(' ', '_')}.docx"
    output_path = os.path.join(output_folder, file_name)
    doc.save(output_path)
    print(f"✅ Resume saved to: {output_path}")
    return output_path

def inline_replacement(paragraph, data):
    full_text = ''.join(run.text for run in paragraph.runs)

    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder in full_text:
            if isinstance(value, list):
                # Format list into bullet point string
                bullet_text = ''
                for item in value:
                    if isinstance(item, str):
                        bullet_text += f"• {item}\n"
                    elif isinstance(item, dict):
                        line = item.get("title", "")
                        if "provider" in item:
                            line += f", {item['provider']}"
                        if "date" in item:
                            line += f" ({item['date']})"
                        bullet_text += f"• {line}\n"
                value = bullet_text.strip()
            elif isinstance(value, dict):
                # Convert dicts (e.g., one project) into formatted string
                formatted = ''
                if 'title' in value and 'description' in value:
                    formatted = f"{value['title']}: {value['description']}"
                else:
                    formatted = json.dumps(value, indent=2)
                value = formatted
            else:
                value = str(value)

            # Replace and rebuild paragraph
            full_text = full_text.replace(placeholder, value)

            for i in range(len(paragraph.runs) - 1, -1, -1):
                paragraph._element.remove(paragraph.runs[i]._element)
            paragraph.add_run(full_text)

def load_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    data = load_json("output/resume_Manjunath.json")  # update path if needed
    data["full_name"] = "Manjunath"  # Ensure it's there for file naming
    fill_resume_template(data)
