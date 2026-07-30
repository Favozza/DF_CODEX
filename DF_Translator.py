import os
import random
import re
import sys
import tkinter as tk
from tkinter import scrolledtext


APP_TITLE = "DF Translator"
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500
WINDOW_GEOMETRY = "500x500"
LANGUAGE_FILES = {
    "Dwarf": "language_DWARF.txt",
    "Elf": "language_ELF.txt",
    "Human": "language_HUMAN.txt",
    "Goblin": "language_GOBLIN.txt",
}
LANGUAGES = ["English", "Dwarf", "Elf", "Human", "Goblin"]
STOP_WORDS = {
    "in",
    "the",
    "a",
    "an",
    "for",
    "of",
    "and",
    "to",
    "is",
    "there",
    "are",
    "on",
    "or",
    "am",
    "lad",
    "as",
    "at",
    "non",
    "dom",
    "use",
    "us",
    "more",
}
SPECIAL_CHARACTERS = [
    "À", "à", "Á", "á", "Â", "â", "Ä", "ä", "Å", "å", "Ç", "ç",
    "È", "è", "É", "é", "Ê", "ê", "Ë", "ë", "Ì", "ì", "Í", "í",
    "Î", "î", "Ï", "ï", "Ñ", "ñ", "Ò", "ò", "Ó", "ó", "Ô", "ô",
    "Ö", "ö", "Ù", "ù", "Ú", "ú", "Û", "û", "Ÿ", "ÿ",
]

# --- Kobold Language Rules & Generator ---
PRIMARY_C1 = [
    "b",
    "d",
    "st",
    "sh",
    "s",
    "t",
    "th",
    "ch",
    "l",
    "f",
    "g",
    "k",
    "p",
    "j",
]
APPROXIMANTS = ["r", "l"]
PRIMARY_VOWELS = ["a", "o", "u", "ay", "ee", "i"]

SECONDARY_C = ["b", "d", "l", "f", "g", "k"]
SECONDARY_VOWELS = ["a", "i", "o", "u"]

FINAL_C = [
    "m",
    "r",
    "ng",
    "b",
    "rb",
    "mb",
    "g",
    "lg",
    "l",
    "lb",
    "lm",
    "k",
    "nk",
    "ld",
    "d",
    "rsn",
]
FINAL_RIMES = ["is", "us", "er", "in"]


def generate_primary_syllable(is_penultimate=False):
    c1 = random.choice(PRIMARY_C1)
    c2 = ""
    if random.random() > 0.5:
        c2_choice = random.choice(APPROXIMANTS)
        if not (c1 == "l" and c2_choice == "l"):
            c2 = c2_choice

    if is_penultimate:
        v = random.choice(PRIMARY_VOWELS)
    else:
        v = random.choice([v for v in PRIMARY_VOWELS if v not in ["ay", "ee"]])

    return c1 + c2 + v, v


def generate_secondary_syllable(vowel):
    c = random.choice(SECONDARY_C)
    return c + vowel


def generate_final_syllable(penult_vowel):
    c = random.choice(FINAL_C)
    available_rimes = FINAL_RIMES
    if penult_vowel in ["ee", "i"]:
        available_rimes = [r for r in FINAL_RIMES if r not in ["er", "in"]]
    r = random.choice(available_rimes)
    return c + r


def generate_kobold_word():
    num_syllables = random.choices([2, 3, 4, 5], weights=[40, 30, 20, 10])[0]
    word_parts = []
    penult_vowel = "a"

    if num_syllables == 2:
        s1, v1 = generate_primary_syllable(is_penultimate=True)
        penult_vowel = v1
        word_parts.append(s1)
    elif num_syllables == 3:
        s1, _ = generate_primary_syllable(is_penultimate=False)
        word_parts.append(s1)
        s2, v2 = generate_primary_syllable(is_penultimate=True)
        penult_vowel = v2
        word_parts.append(s2)
    elif num_syllables == 4:
        s1, _ = generate_primary_syllable(is_penultimate=False)
        word_parts.append(s1)
        v_base = next(v for v in PRIMARY_VOWELS if s1.endswith(v))
        word_parts.append(generate_secondary_syllable(v_base))
        s3, v3 = generate_primary_syllable(is_penultimate=True)
        penult_vowel = v3
        word_parts.append(s3)
    elif num_syllables == 5:
        s1, _ = generate_primary_syllable(is_penultimate=False)
        word_parts.append(s1)
        v_base = next(v for v in PRIMARY_VOWELS if s1.endswith(v))
        word_parts.append(generate_secondary_syllable(v_base))
        word_parts.append(generate_secondary_syllable(v_base))
        s4, v4 = generate_primary_syllable(is_penultimate=True)
        penult_vowel = v4
        word_parts.append(s4)

    word_parts.append(generate_final_syllable(penult_vowel))
    return "".join(word_parts).capitalize()


def generate_kobold_sentence(word_count=6):
    special_words = ["AUGIS", "STORKIS", "STRANGUS"]
    sentence = []
    for _ in range(word_count):
        if random.random() < 0.005:
            sentence.append(random.choice(special_words))
        else:
            sentence.append(generate_kobold_word())
    return " ".join(sentence) + "."


# --- Divine Language Rules & Generator (Based on Dwarf Fortress Wiki) ---
DIVINE_VOWEL_LOOKUP = [
    "a", "e", "i", "o", "u",
    "ae", "ai", "ao", "au", "ea", "ei", "eo", "eu", "ia", "ie", "io", "iu",
    "oa", "oe", "oi", "ou", "ua", "ue", "ui", "uo", "ah", "eh", "ih", "oh",
    "uh", "ay", "ey", "iy", "oy", "uy"
]
DIVINE_CONS_LOOKUP = [
    "b", "p", "g", "k", "c", "z", "s", "d", "t", "m", "n", "ng",
    "v", "f", "w", "h", "j", "l", "r", "q", "x", "y"
]


def generate_divine_letter(lookup_list, common_num, total_num):
    # 80% chance (not 0 in 5) to pick from common pool if simulated,
    # approximating the script logic: trandom(5) != 0 -> common else rare
    if random.randint(0, 4) != 0:
        return random.choice(lookup_list[:common_num])
    else:
        return random.choice(lookup_list[:total_num])


def generate_divine_word():
    # Consonants: 12 common out of 22 total
    # Vowels: 5 common out of 35 total
    str_val = ""
    if random.randint(0, 1) != 0:
        str_val += generate_divine_letter(DIVINE_CONS_LOOKUP, 12, 22)
        str_val += generate_divine_letter(DIVINE_VOWEL_LOOKUP, 5, 35)
    else:
        str_val += generate_divine_letter(DIVINE_VOWEL_LOOKUP, 5, 35)

    num_letters = random.randint(0, 2)
    str_val += generate_divine_letter(DIVINE_CONS_LOOKUP, 12, 22)
    if num_letters > 0:
        str_val += generate_divine_letter(DIVINE_VOWEL_LOOKUP, 5, 35)
    if num_letters > 1:
        str_val += generate_divine_letter(DIVINE_CONS_LOOKUP, 12, 22)

    return str_val.capitalize()


def generate_divine_sentence(word_count=6):
    sentence = [generate_divine_word() for _ in range(word_count)]
    return " ".join(sentence) + "."


def resource_path(relative_path):
    """Return the absolute path to a bundled or local resource."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_dict(filename):
    dictionary = {}
    reverse_dictionary = {}
    path = resource_path(filename)

    if os.path.exists(path):
        with open(path, "r", encoding="cp437", errors="ignore") as file_handle:
            for match in re.finditer(r"\[T_WORD:([^:]+):([^\]]+)\]", file_handle.read()):
                english_word = match.group(1).strip()
                fantasy_word = match.group(2).strip().lower()
                dictionary[english_word] = fantasy_word
                if fantasy_word not in reverse_dictionary:
                    reverse_dictionary[fantasy_word] = english_word.lower()

    return dictionary, reverse_dictionary


def load_all_dictionaries():
    dictionaries = {}
    reverse_dictionaries = {}

    for language_name, filename in LANGUAGE_FILES.items():
        dictionary, reverse_dictionary = load_dict(filename)
        dictionaries[language_name] = dictionary
        reverse_dictionaries[language_name] = reverse_dictionary

    return dictionaries, reverse_dictionaries


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    center_x = int(screen_width / 2 - width / 2)
    center_y = int(screen_height / 2 - height / 2)
    window.geometry(f"{width}x{height}+{center_x}+{center_y}")


def english_candidates(word):
    candidates = [word]

    if word.endswith("IES") and len(word) > 3:
        candidates.append(word[:-3] + "Y")
    if word.endswith("IED") and len(word) > 3:
        candidates.append(word[:-3] + "Y")
    if word.endswith("ES") and len(word) > 2:
        candidates.append(word[:-2])
    if word.endswith("ED") and len(word) > 2:
        candidates.append(word[:-2])
        candidates.append(word[:-1])
    if word.endswith("ING") and len(word) > 3:
        candidates.append(word[:-3])
        candidates.append(word[:-3] + "E")
    if word.endswith("S") and len(word) > 1:
        candidates.append(word[:-1])

    return candidates


def fantasy_candidates(word):
    candidates = [word]

    if word.endswith("es") and len(word) > 2:
        candidates.append(word[:-2])
    if word.endswith("s") and len(word) > 1:
        candidates.append(word[:-1])

    return candidates


class AutoText(scrolledtext.ScrolledText):

    def __init__(self, master, get_d, get_mode_type, **kwargs):
        kwargs.setdefault("undo", True)
        super().__init__(master, **kwargs)
        self.get_d = get_d
        self.get_mode_type = get_mode_type
        self.popup = None
        self.lb = None
        self.suppress_popup = False

        self.tag_configure("untranslated", foreground="red")

        self.bind("<KeyRelease>", self.chk)
        self.bind("<Tab>", lambda event: self.sel() or "break")
        self.bind("<Return>", self.handle_return)
        self.bind("<Down>", self.focus_lb)
        self.bind("<Configure>", lambda event: self.hide_popup())
        self.bind("<Control-z>", self.undo_action)
        self.bind("<Control-y>", self.redo_action)
        self.bind("<Control-Shift-Z>", self.redo_action)
        self.bind("<Escape>", self.close_popup_event)

    def undo_action(self, _event):
        try:
            self.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def redo_action(self, _event):
        try:
            self.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def chk(self, event):
        if not self.winfo_exists():
            return

        if self.suppress_popup:
            if event.keysym in ("Escape", "Left", "Right", "Up", "Down", "Shift_L", "Shift_R"):
                return
            self.suppress_popup = False

        if event.keysym in ("Left", "Right", "Up", "Down", "Return", "Tab", "Shift_L", "Shift_R", "BackSpace"):
            if event.keysym == "BackSpace":
                word_match = re.search(r"\b(\w+)\Z", self.get("1.0", tk.INSERT))
                if not word_match:
                    self.hide_popup()
                    return

        word_match = re.search(r"\b(\w+)\Z", self.get("1.0", tk.INSERT))
        try:
            dictionary = self.get_d()
        except Exception:
            return

        mode_type = self.get_mode_type()
        if word_match and dictionary:
            prefix = word_match.group(1)
            if mode_type == "eng_to_fan":
                matches = [key for key in sorted(dictionary) if key.startswith(prefix.upper())]
            else:
                matches = [key for key in sorted(dictionary) if key.startswith(prefix.lower())]

            if matches:
                self.show_popup(matches, dictionary)
                return

        self.hide_popup()

    def show_popup(self, matches, dictionary):
        self.hide_popup()

        try:
            self.popup = tk.Toplevel(self)
            self.popup.wm_overrideredirect(True)

            bbox = self.bbox(tk.INSERT)
            if not bbox:
                self.hide_popup()
                return

            x_pos, y_pos, _width, height = bbox
            root_x = self.winfo_rootx() + x_pos
            root_y = self.winfo_rooty() + y_pos + height + 2
            self.popup.geometry(f"+{root_x}+{root_y}")

            self.lb = tk.Listbox(
                self.popup,
                height=min(len(matches), 7),
                exportselection=False,
                font=("Arial", 9),
                bg="#ffffcc",
            )
            self.lb.pack(fill=tk.BOTH, expand=True)

            for key in matches:
                self.lb.insert(tk.END, f"{key} -> {dictionary.get(key, '')}")

            self.lb.bind("<Return>", lambda event: self.sel())
            self.lb.bind("<Tab>", lambda event: self.sel())
            self.lb.bind("<ButtonRelease-1>", lambda event: self.sel())
            self.lb.selection_set(0)
        except Exception:
            self.hide_popup()

    def hide_popup(self):
        if self.popup:
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
            self.lb = None

    def focus_lb(self, _event):
        if self.lb:
            try:
                self.lb.focus_set()
                self.lb.selection_set(0)
            except Exception:
                pass
            return "break"

    def sel(self):
        if self.lb:
            try:
                selection = self.lb.curselection()
                if selection:
                    key = self.lb.get(selection[0]).split(" -> ")[0]
                    word_match = re.search(r"\b(\w+)\Z", self.get("1.0", tk.INSERT))
                    if word_match:
                        self.delete(f"insert-{len(word_match.group(1))}c", tk.INSERT)
                        self.insert(tk.INSERT, key + " ")
            except Exception:
                pass
            self.hide_popup()
            self.focus_set()
            return "break"

    def handle_return(self, _event):
        return None

    def close_popup_event(self, _event):
        if self.popup:
            self.suppress_popup = True
            self.hide_popup()
            return "break"
        return None


def lookup_single(token, target_dict, source_reverse_dict, mode_type):
    is_capitalized = token.istitle()
    is_upper = token.isupper()

    result = None
    if mode_type == "eng_to_fan":
        upper_token = token.upper()
        if upper_token in target_dict:
            result = target_dict[upper_token]
        else:
            for candidate in english_candidates(upper_token):
                if candidate in target_dict:
                    result = target_dict[candidate]
                    break
    elif mode_type == "fan_to_eng":
        lower_token = token.lower()
        if lower_token in source_reverse_dict:
            result = source_reverse_dict[lower_token]
        else:
            for candidate in fantasy_candidates(lower_token):
                if candidate in source_reverse_dict:
                    result = source_reverse_dict[candidate]
                    break
    else:
        lower_token = token.lower()
        english_word = None
        for candidate in fantasy_candidates(lower_token):
            if candidate in source_reverse_dict:
                english_word = source_reverse_dict[candidate]
                break
        if english_word:
            upper_token = english_word.upper()
            if upper_token in target_dict:
                result = target_dict[upper_token]

    if result:
        if is_upper:
            return result.upper()
        elif is_capitalized:
            return result.capitalize()
    return result


def translate_word(token, target_dict, source_reverse_dict, mode_type):
    direct_translation = lookup_single(token, target_dict, source_reverse_dict, mode_type)
    if direct_translation:
        return direct_translation

    base_token = token.upper() if mode_type == "eng_to_fan" else token.lower()
    for index in range(2, len(base_token) - 1):
        left_part = base_token[:index]
        right_part = base_token[index:]
        left_translation = lookup_single(left_part, target_dict, source_reverse_dict, mode_type)
        if not left_translation:
            continue

        right_translation = lookup_single(right_part, target_dict, source_reverse_dict, mode_type)
        if not right_translation:
            continue

        combined = left_translation + right_translation
        if is_upper:
            return combined.upper()
        elif is_capitalized:
            return combined.capitalize()
        return combined

    return None


def main():
    dicts, rev_dicts = load_all_dictionaries()

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_GEOMETRY)
    center_window(root, WINDOW_WIDTH, WINDOW_HEIGHT)

    try:
        root.iconbitmap(resource_path("dftranslogo.ico"))
    except Exception:
        pass

    def on_closing():
        try:
            root.quit()
            root.destroy()
        except Exception:
            sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # --- Top Navigation Bar for Switching Interfaces (Placed First) ---
    nav_bar = tk.Frame(root, bg="#e0e0e0", height=45)
    nav_bar.pack(side=tk.TOP, fill=tk.X)

    btn_translations = tk.Button(
        nav_bar,
        text="Translations",
        font=("Arial", 10, "bold"),
        width=15,
        command=lambda: show_frame(trans_frame),
    )
    btn_translations.pack(side=tk.LEFT, padx=8, pady=6)

    btn_kobol = tk.Button(
        nav_bar,
        text="Kobold",
        font=("Arial", 10, "bold"),
        width=12,
        command=lambda: show_frame(kobold_frame),
    )
    btn_kobol.pack(side=tk.LEFT, padx=8, pady=6)

    btn_divine = tk.Button(
        nav_bar,
        text="Divine",
        font=("Arial", 10, "bold"),
        width=12,
        command=lambda: show_frame(divine_frame),
    )
    btn_divine.pack(side=tk.LEFT, padx=8, pady=6)

    # --- Container for Main Content Frames ---
    container = tk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True)

    trans_frame = tk.Frame(container)
    kobold_frame = tk.Frame(container)
    divine_frame = tk.Frame(container)

    for frame in (trans_frame, kobold_frame, divine_frame):
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_frame(frame):
        frame.tkraise()

    # ==================== TRANSLATIONS INTERFACE ====================
    in_lang_var = tk.StringVar(trans_frame, "English")
    out_lang_var = tk.StringVar(trans_frame, "Dwarf")

    def get_mode_type():
        input_language = in_lang_var.get()
        output_language = out_lang_var.get()
        if input_language == "English" and output_language != "English":
            return "eng_to_fan"
        if input_language != "English" and output_language == "English":
            return "fan_to_eng"
        return "fan_to_fan"

    def get_active_dicts():
        input_language = in_lang_var.get()
        output_language = out_lang_var.get()
        mode_type = get_mode_type()

        if mode_type == "eng_to_fan":
            return dicts[output_language], None
        if mode_type == "fan_to_eng":
            return None, rev_dicts[input_language]
        return dicts[output_language], rev_dicts[input_language]

    def update_labels():
        in_label.config(text=f"Input ({in_lang_var.get()}):")
        out_label.config(text=f"Output ({out_lang_var.get()}):")

    def get_phrase_dictionary(mode_type, target_dict, source_reverse_dict):
        if mode_type == "eng_to_fan":
            return target_dict
        return source_reverse_dict

    def translate_phrase_matches(line, phrase_dict):
        working_line = line
        phrase_keys = sorted((key for key in phrase_dict if " " in key), key=len, reverse=True)
        for phrase_key in phrase_keys:
            translated_value = phrase_dict.get(phrase_key)
            pattern = re.compile(re.escape(phrase_key), re.IGNORECASE)
            working_line = pattern.sub(translated_value, working_line)
        return working_line

    def is_known_allowed_word(token):
        token_lower = token.lower()
        if token_lower in STOP_WORDS:
            return False

        for language_name, dictionary in dicts.items():
            reverse_dictionary = rev_dicts[language_name]
            if (
                token_lower in dictionary
                or token_lower in dictionary.values()
                or token_lower in reverse_dictionary
                or token_lower in reverse_dictionary.values()
            ):
                return True

        return False

    def trans(*_args):
        try:
            if not root.winfo_exists() or not out_box.winfo_exists():
                return
        except Exception:
            return

        in_box.tag_remove("untranslated", "1.0", tk.END)

        mode_type = get_mode_type()
        target_dict, source_reverse_dict = get_active_dicts()
        phrase_dict = get_phrase_dictionary(mode_type, target_dict, source_reverse_dict)
        input_text = in_box.get("1.0", tk.END)
        translated_lines = []

        for line_index, line in enumerate(input_text.splitlines(), start=1):
            working_line = translate_phrase_matches(line, phrase_dict)
            translated_words = []

            for match in re.finditer(r"\b\w+\b", working_line):
                token = match.group(0)
                start_col = match.start()
                end_col = match.end()
                translated_word = translate_word(token, target_dict, source_reverse_dict, mode_type)

                if translated_word:
                    translated_words.append(translated_word)
                    continue

                if is_known_allowed_word(token):
                    translated_words.append(token)
                    continue

                in_box.tag_add("untranslated", f"{line_index}.{start_col}", f"{line_index}.{end_col}")

            translated_lines.append(" ".join(translated_words))

        try:
            out_box.delete("1.0", tk.END)
            out_box.insert(tk.END, "\n".join(translated_lines))
        except Exception:
            pass

    last_in_lang = in_lang_var.get()
    last_out_lang = out_lang_var.get()
    is_reverting = False

    def on_in_lang_change(*_args):
        nonlocal last_in_lang, is_reverting
        if is_reverting:
            return

        current_input = in_lang_var.get()
        if current_input == out_lang_var.get():
            is_reverting = True
            in_lang_var.set(last_in_lang)
            is_reverting = False
            return

        if current_input != last_in_lang:
            last_in_lang = current_input
            in_box.delete("1.0", tk.END)
            out_box.delete("1.0", tk.END)

        update_labels()
        trans()

    def on_out_lang_change(*_args):
        nonlocal last_out_lang, is_reverting
        if is_reverting:
            return

        current_output = out_lang_var.get()
        if current_output == in_lang_var.get():
            is_reverting = True
            out_lang_var.set(last_out_lang)
            is_reverting = False
            return

        if current_output != last_out_lang:
            last_out_lang = current_output

        update_labels()
        trans()

    in_lang_var.trace_add("write", on_in_lang_change)
    out_lang_var.trace_add("write", on_out_lang_change)

    def set_box_text(text_box, text):
        stripped_text = text.strip()
        text_box.delete("1.0", tk.END)
        text_box.insert("1.0", stripped_text + ("\n" if stripped_text else ""))

    def swap_languages_and_content():
        nonlocal is_reverting, last_in_lang, last_out_lang

        is_reverting = True
        current_input = in_lang_var.get()
        current_output = out_lang_var.get()

        in_lang_var.set(current_output)
        out_lang_var.set(current_input)
        last_in_lang = current_output
        last_out_lang = current_input
        is_reverting = False

        input_text = in_box.get("1.0", tk.END)
        output_text = out_box.get("1.0", tk.END)
        set_box_text(in_box, output_text)
        set_box_text(out_box, input_text)

        update_labels()
        trans()

    top_frame = tk.Frame(trans_frame)
    top_frame.pack(padx=15, pady=10, fill=tk.X)

    center_container = tk.Frame(top_frame)
    center_container.pack(anchor=tk.CENTER)

    tk.Label(center_container, text="Input/reset:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 2))
    in_menu = tk.OptionMenu(center_container, in_lang_var, *LANGUAGES)
    in_menu.pack(side=tk.LEFT, padx=(0, 10))

    swap_btn = tk.Button(
        center_container,
        text="⇄",
        font=("Arial", 13),
        width=3,
        command=swap_languages_and_content,
    )
    swap_btn.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(center_container, text="Output:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 2))
    out_menu = tk.OptionMenu(center_container, out_lang_var, *LANGUAGES)
    out_menu.pack(side=tk.LEFT)

    in_label = tk.Label(trans_frame, text="Input (English):", font=("Arial", 10, "bold"))
    in_label.pack(anchor="w", padx=15)

    chars_frame = tk.Frame(trans_frame)
    chars_frame.pack(fill=tk.X, padx=15, pady=2)

    def insert_char(char):
        in_box.insert(tk.INSERT, char)
        in_box.focus_set()

    for index, character in enumerate(SPECIAL_CHARACTERS):
        row_index = index // 19
        col_index = index % 19
        button = tk.Button(
            chars_frame,
            text=character,
            width=2,
            font=("Arial", 8),
            command=lambda current_char=character: insert_char(current_char),
        )
        button.grid(row=row_index, column=col_index, padx=1, pady=1)

    in_box = AutoText(
        trans_frame,
        lambda: get_active_dicts()[0] if get_mode_type() == "eng_to_fan" else get_active_dicts()[1],
        get_mode_type,
        height=1,
        wrap=tk.WORD,
        font=("Arial", 11),
    )
    in_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    tk.Button(
        trans_frame,
        text="Translate",
        command=trans,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
    ).pack(pady=5)

    out_label = tk.Label(trans_frame, text="Output (Dwarf):", font=("Arial", 10, "bold"))
    out_label.pack(anchor="w", padx=15)

    out_box = scrolledtext.ScrolledText(
        trans_frame,
        height=1,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#f4f4f4",
    )
    out_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    def show_email_dialog():
        dialog = tk.Toplevel(root)
        dialog.title("Contact Support")
        dialog.geometry("320x130")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        dialog.update_idletasks()
        x_pos = root.winfo_rootx() + (root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y_pos = root.winfo_rooty() + (root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x_pos}+{y_pos}")

        tk.Label(dialog, text="You can reach me at:", font=("Arial", 9)).pack(pady=(15, 5))

        email_entry = tk.Entry(dialog, font=("Arial", 10), justify="center", width=30)
        email_entry.insert(0, "favthebest@hotmail.it")
        email_entry.config(state="readonly")
        email_entry.pack(pady=5)

        tk.Button(dialog, text="Close", command=dialog.destroy, width=10).pack(pady=(5, 10))

    tk.Button(
        trans_frame,
        text="Facing an issue? Write me!",
        command=show_email_dialog,
        font=("Arial", 9),
        fg="red",
        cursor="hand2",
    ).pack(pady=(0, 10))

    # ==================== KOBOL (KOBOLD) INTERFACE ====================
    tk.Label(
        kobold_frame,
        text="Kobold Gibberish Generator",
        font=("Arial", 12, "bold"),
    ).pack(pady=15)

    options_frame = tk.Frame(kobold_frame)
    options_frame.pack(pady=5)

    tk.Label(options_frame, text="Words in sentence:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    word_count_scale = tk.Scale(options_frame, from_=1, to=50, orient=tk.HORIZONTAL)
    word_count_scale.set(5)
    word_count_scale.pack(side=tk.LEFT, padx=5)

    kobold_output_box = scrolledtext.ScrolledText(
        kobold_frame,
        height=8,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#f4f4f4",
    )
    kobold_output_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    def generate_and_display_kobold():
        count = word_count_scale.get()
        sentence = generate_kobold_sentence(count)
        kobold_output_box.insert(tk.END, sentence + "\n")
        kobold_output_box.see(tk.END)

    def clear_kobold_output():
        kobold_output_box.delete("1.0", tk.END)

    btn_gen_kobold = tk.Button(
        kobold_frame,
        text="Generate Sentence",
        command=generate_and_display_kobold,
        bg="#2196F3",
        fg="white",
        font=("Arial", 10, "bold"),
    )
    btn_gen_kobold.pack(pady=5)

    btn_clear_kobold = tk.Button(
        kobold_frame,
        text="Clear Output",
        command=clear_kobold_output,
        font=("Arial", 9),
    )
    btn_clear_kobold.pack(pady=(0, 15))

    # ==================== DIVINE LANGUAGE INTERFACE ====================
    tk.Label(
        divine_frame,
        text="Divine Language Generator",
        font=("Arial", 12, "bold"),
    ).pack(pady=15)

    divine_options_frame = tk.Frame(divine_frame)
    divine_options_frame.pack(pady=5)

    tk.Label(divine_options_frame, text="Words in sentence:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    divine_word_count_scale = tk.Scale(divine_options_frame, from_=1, to=50, orient=tk.HORIZONTAL)
    divine_word_count_scale.set(5)
    divine_word_count_scale.pack(side=tk.LEFT, padx=5)

    divine_output_box = scrolledtext.ScrolledText(
        divine_frame,
        height=8,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#f4f4f4",
    )
    divine_output_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    def generate_and_display_divine():
        count = divine_word_count_scale.get()
        sentence = generate_divine_sentence(count)
        divine_output_box.insert(tk.END, sentence + "\n")
        divine_output_box.see(tk.END)

    def clear_divine_output():
        divine_output_box.delete("1.0", tk.END)

    btn_gen_divine = tk.Button(
        divine_frame,
        text="Generate Sentence",
        command=generate_and_display_divine,
        bg="#9C27B0",
        fg="white",
        font=("Arial", 10, "bold"),
    )
    btn_gen_divine.pack(pady=5)

    btn_clear_divine = tk.Button(
        divine_frame,
        text="Clear Output",
        command=clear_divine_output,
        font=("Arial", 9),
    )
    btn_clear_divine.pack(pady=(0, 15))

    # Set initial active view to Translations
    show_frame(trans_frame)

    root.mainloop()


if __name__ == "__main__":
    main()