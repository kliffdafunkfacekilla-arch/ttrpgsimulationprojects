import os
import shutil
import sys
from pathlib import Path

# Setup directories to scan
LORE_DIR = Path(__file__).parent.parent / "shatterlands_simulator" / "data" / "lore"
COMPILED_BOOK_DIR = Path(__file__).parent.parent / "Compiled_Book"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_all_lore_files(base_dirs):
    files = []
    for d in base_dirs:
        if d.exists():
            for ext in ['*.md', '*.docx', '*.txt']:
                files.extend(d.rglob(ext))
    return files

def ensure_category_dir(base_dir, category_name):
    cat_dir = base_dir / category_name
    cat_dir.mkdir(exist_ok=True)
    return cat_dir

def main():
    dirs_to_scan = [LORE_DIR, COMPILED_BOOK_DIR]
    print(f"--- Welcome to the Lore Organizer ---")
    
    files = get_all_lore_files(dirs_to_scan)
    print(f"Found {len(files)} documents to review across {len(dirs_to_scan)} directories.\n")
    
    if len(files) == 0:
        return

    input("Press Enter to begin reviewing files...")

    for i, file_path in enumerate(files, 1):
        clear_screen()
        print(f"Document {i} of {len(files)}")
        print(f"File Name: {file_path.name}")
        print(f"Directory: {file_path.parent}")
        print("-" * 40)
        
        while True:
            print("\nWhat would you like to do with this file?")
            print("  1. Keep / Skip (do nothing)")
            print("  2. Rename")
            print("  3. Move to a Category Folder")
            print("  4. Delete")
            print("  5. Quit App")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                print("Skipping file.")
                break
            elif choice == '2':
                new_name = input(f"Enter new name (current is {file_path.name}): ").strip()
                if new_name:
                    new_path = file_path.parent / new_name
                    try:
                        file_path.rename(new_path)
                        print(f"Renamed to {new_name}")
                        file_path = new_path # Update reference
                    except Exception as e:
                        print(f"Error renaming: {e}")
            elif choice == '3':
                category = input("Enter category folder name (e.g., 'Factions', 'Locations'): ").strip()
                if category:
                    cat_dir = ensure_category_dir(file_path.parent, category)
                    new_path = cat_dir / file_path.name
                    try:
                        shutil.move(str(file_path), str(new_path))
                        print(f"Moved to {category}/{file_path.name}")
                        break
                    except Exception as e:
                        print(f"Error moving: {e}")
            elif choice == '4':
                confirm = input("Are you sure you want to delete this file? (y/n): ").strip().lower()
                if confirm == 'y':
                    try:
                        file_path.unlink()
                        print("File deleted.")
                        break
                    except Exception as e:
                        print(f"Error deleting: {e}")
            elif choice == '5':
                print("Exiting organizer...")
                sys.exit(0)
            else:
                print("Invalid choice. Please select 1-5.")

    print("\n--- All done! ---")

if __name__ == "__main__":
    main()
