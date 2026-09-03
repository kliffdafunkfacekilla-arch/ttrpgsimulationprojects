import os
import re
import json

def compile_wiki_manifest():
    chapters_dir = r"c:\Users\krazy\Desktop\ostraka-wiki\public\chapters"
    final_vault_dir = r"c:\Users\krazy\Documents\shatterlands\01_Final_Obsidian_Vault"
    output_manifest = r"c:\Users\krazy\Desktop\ostraka-wiki\public\data\slides_manifest.json"
    
    slides = []
    slide_id = 0
    
    # 1. Check if Chapter files are present in public/chapters
    has_chapters = False
    if os.path.exists(chapters_dir):
        chapter_files = [f for f in os.listdir(chapters_dir) if f.startswith("Chapter_") and f.endswith(".md")]
        if chapter_files:
            has_chapters = True
            
    if has_chapters:
        print("[~] Compiling web wiki from Chapter files...")
        filenames = sorted(chapter_files)
        for fname in filenames:
            path = os.path.join(chapters_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            chapter_title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            chapter_title = chapter_title_match.group(1).strip() if chapter_title_match else fname
            
            sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
            for sec in sections[1:]:
                lines = sec.split("\n")
                section_title = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
                
                # Extract first image tag
                img_match = re.search(r"!\[.*?\]\((.*?)\)", body)
                illustration_url = ""
                if img_match:
                    img_url = img_match.group(1)
                    if not img_url.startswith("/"):
                        img_url = "/" + img_url
                    illustration_url = img_url
                    body = re.sub(r"!\[.*?\]\(.*?\)\s*", "", body, count=1).strip()
                    
                era_map = "/map_full.png"
                if "Chapter_01" in fname or "Chapter_02" in fname:
                    era_map = "/map_fae_era.png"
                elif "Chapter_03" in fname:
                    era_map = "/map_magister_era.png"
                    
                section_slug = section_title.lower().replace(" ", "_")
                section_slug = re.sub(r"[^a-z0-9_]", "", section_slug)
                
                slides.append({
                    "id": slide_id,
                    "chapter_file": fname,
                    "chapter_title": chapter_title,
                    "section_title": section_title,
                    "section_slug": section_slug,
                    "body_markdown": body,
                    "era_map": era_map,
                    "illustration": illustration_url
                })
                slide_id += 1
    else:
        # 2. Fallback: Parse the compiled Obsidian Vault folders as chapters
        print("[~] No chapters folder found. Compiling web wiki from Obsidian Vault folders...")
        if not os.path.exists(final_vault_dir):
            print(f"[-] Obsidian Vault folder not found: {final_vault_dir}")
            return False
            
        # Scan subdirectories under final vault
        subdirs = sorted([d for d in os.listdir(final_vault_dir) if os.path.isdir(os.path.join(final_vault_dir, d)) and d != "images"])
        
        for sdir in subdirs:
            chapter_title = sdir.replace("_", " ").title()
            sdir_path = os.path.join(final_vault_dir, sdir)
            
            note_files = sorted([f for f in os.listdir(sdir_path) if f.endswith(".md")])
            for nfile in note_files:
                path = os.path.join(sdir_path, nfile)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Strip YAML Frontmatter if present
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        content = parts[2].strip()
                        
                # Extract first heading as section title, fallback to filename
                heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                section_title = heading_match.group(1).strip() if heading_match else nfile.replace(".md", "")
                
                # Strip title heading from body to prevent duplication
                body = re.sub(r"^#\s+.+$", "", content, count=1, flags=re.MULTILINE).strip()
                
                # Find first image embed
                # Handles both markdown images `![](url)` and wiki links `![[image.png]]` or `![alt](../images/url)`
                img_match = re.search(r"!\[.*?\]\((.*?)\)", body)
                wiki_img_match = re.search(r"!\[\[(.*?)\]\]", body)
                
                illustration_url = ""
                if img_match:
                    img_url = img_match.group(1)
                    # Convert standard relative path
                    if "../images/" in img_url:
                        img_url = img_url.replace("../images/", "/illustrations/")
                    if not img_url.startswith("/"):
                        img_url = "/" + img_url
                    illustration_url = img_url
                    body = re.sub(r"!\[.*?\]\(.*?\)\s*", "", body, count=1).strip()
                elif wiki_img_match:
                    img_name = wiki_img_match.group(1)
                    illustration_url = f"/illustrations/{img_name}"
                    body = re.sub(r"!\[\[.*?\]\]\s*", "", body, count=1).strip()
                    
                era_map = "/map_full.png"
                section_slug = section_title.lower().replace(" ", "_")
                section_slug = re.sub(r"[^a-z0-9_]", "", section_slug)
                
                slides.append({
                    "id": slide_id,
                    "chapter_file": nfile,
                    "chapter_title": chapter_title,
                    "section_title": section_title,
                    "section_slug": section_slug,
                    "body_markdown": body,
                    "era_map": era_map,
                    "illustration": illustration_url
                })
                slide_id += 1
                
    # Save the manifest
    output_dir = os.path.dirname(output_manifest)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_manifest, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)
        
    print(f"[+] Web wiki manifest successfully compiled with {len(slides)} sections to: {output_manifest}")
    return True

if __name__ == "__main__":
    compile_wiki_manifest()
