# openai_pdf_md.py
# openai converts pdf's to markdown files using vision parser
# this script requires an api key for openai and vision parser
# the api key is stored in the .env file


from vision_parse import VisionParser # convert pdf to markdown
from dotenv import load_dotenv
import os 

load_dotenv()


input_dir  = "input"
output_dir = "output"



# Initialize parser with OpenAI model
parser = VisionParser(
    model_name="gpt-4o-mini",
    api_key= os.environ['OPENAI_API_KEY'], 
    temperature=0.7,
    top_p=0.4,
    image_mode="url",
    detailed_extraction=False,
    enable_concurrency=True,
)



# loop through all PDFs in Files_to_Convert
for pdf_name in os.listdir(input_dir):
    if not pdf_name.lower().endswith(".pdf"):
        continue

    # build file-system path to PDF folder
    pdf_path = os.path.join(input_dir, pdf_name)

    # convert pdf to markdown and join
    pages = parser.convert_pdf(pdf_path)
    full_md = "\n\n".join(pages) # join all 

    # build output path
    base    = os.path.splitext(pdf_name)[0]
    out_md  = f"{base}.md"
    out_path = os.path.join(output_dir, out_md)

    # opens a file and writes your markdown text into it
    with open(out_path,"w") as f: # the w means "write"
        f.write(full_md)

    # confirmation message 
    print(f"Wrote combined markdown to {out_path}")


