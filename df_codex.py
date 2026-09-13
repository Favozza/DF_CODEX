import gzip, os, random, re, sys, unicodedata
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk


# ###############################################################################################################
# ########################################## INITIALIZATION #####################################################
# ###############################################################################################################
# --- Tool Window ---
APP_TITLE = "DF CODEX - Dwarf Fortress CanOn Dictionary EXplorer"
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 700
WINDOW_GEOMETRY = "600x700"

# --- Upload ---
LANGUAGE_FILES = {
    "Dwarf": "language_DWARF.txt",
    "Elf": "language_ELF.txt",
    "Human": "language_HUMAN.txt",
    "Goblin": "language_GOBLIN.txt",
}

# --- Languages and Settings ---
LANGUAGES = ["English", "Dwarf", "Elf", "Human", "Goblin"]
STOP_WORDS = {
    "in", "the", "a", "an", "for", "of", "and",
    "to", "is", "there", "are", "on", "or", "am",
    "lad", "as", "at", "non", "dom", "use", "us", "more",
}
SPECIAL_CHARACTERS = [
    "À", "à", "Á", "á", "Â", "â", "Ä", "ä", "Å", "å", "Ç", "ç",
    "È", "è", "É", "é", "Ê", "ê", "Ë", "ë", "Ì", "ì", "Í", "í",
    "Î", "î", "Ï", "ï", "Ñ", "ñ", "Ò", "ò", "Ó", "ó", "Ô", "ô",
    "Ö", "ö", "Ù", "ù", "Ú", "ú", "Û", "û", "Ÿ", "ÿ",
]

# --- Kobold Language ---
PRIMARY_C1 = [
    "b", "d", "st", "sh", "s", "t", "th",
    "ch", "l", "f", "g", "k", "p", "j",
]
APPROXIMANTS = ["r", "l"]
PRIMARY_VOWELS = ["a", "o", "u", "ay", "ee", "i"]
SECONDARY_C = ["b", "d", "l", "f", "g", "k"]
SECONDARY_VOWELS = ["a", "i", "o", "u"]
FINAL_C = [
    "m", "r", "ng", "b", "rb", "mb", "g",
    "lg", "l", "lb", "lm", "k", "nk", "ld", "d", "rsn",
]
FINAL_RIMES = ["is", "us", "er", "in"]

# --- Divine Language ---
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


# ###############################################################################################################
# ############################################## FUNCTIONS ######################################################
# ###############################################################################################################
# --- Kobold Functions ---
def generate_primary_syllable(is_penultimate=False):
    """Build one "primary" Kobold syllable (consonant + optional approximant
    + vowel). When `is_penultimate` is True the diphthong-like vowels ("ay",
    "ee") are allowed; otherwise they're excluded so they only ever land on
    the syllable right before the word's final syllable. Returns a tuple of
    (syllable_text, vowel_used)."""
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
    """Build a "secondary" (mid-word, unstressed) Kobold syllable by pairing
    a random secondary consonant with the given vowel, echoing the vowel of
    a neighboring primary syllable."""
    c = random.choice(SECONDARY_C)
    return c + vowel

def generate_final_syllable(penult_vowel):
    """Build the closing syllable of a Kobold word: a random final consonant
    cluster plus a rime. If the preceding (penultimate) vowel was "ee" or
    "i", the rimes "er"/"in" are excluded to avoid awkward-sounding
    combinations."""
    c = random.choice(FINAL_C)
    available_rimes = FINAL_RIMES
    if penult_vowel in ["ee", "i"]:
        available_rimes = [r for r in FINAL_RIMES if r not in ["er", "in"]]
    r = random.choice(available_rimes)
    return c + r

def generate_kobold_word():
    """Randomly assemble a full Kobold word (2-5 syllables, weighted toward
    shorter words) out of primary, secondary and final syllables, tracking
    the penultimate vowel so the final syllable's rime stays consistent with
    it. Returns the word capitalized."""
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
    """Generate a lowercase, space-joined "sentence" of `word_count`
    made-up Kobold words, occasionally (about 0.5% chance per word)
    substituting one of a few fixed special words instead."""
    special_words = ["augis", "storkis", "strangus"]
    sentence = []
    for _ in range(word_count):
        if random.random() < 0.005:
            sentence.append(random.choice(special_words))
        else:
            sentence.append(generate_kobold_word().lower())
    return " ".join(sentence)


# --- Divine Functions ---
def generate_divine_letter(lookup_list, common_num, total_num):
    """Pick one letter/phoneme from `lookup_list`. With an 80% chance draw
    from the first `common_num` ("common") entries; otherwise draw from the
    full `total_num`-entry pool, letting rarer sounds show up occasionally."""
    # 80% chance (not 0 in 5) to pick from common pool if simulated,
    # approximating the script logic: trandom(5) != 0 -> common else rare
    if random.randint(0, 4) != 0:
        return random.choice(lookup_list[:common_num])
    else:
        return random.choice(lookup_list[:total_num])

def generate_divine_word():
    """Randomly assemble a short "Divine language" word out of
    consonant/vowel letters (favoring the common subsets via
    generate_divine_letter), with a random amount of trailing letters.
    Returns the word capitalized."""
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
    """Generate a lowercase, space-joined "sentence" of `word_count`
    made-up Divine-language words."""
    sentence = [generate_divine_word().lower() for _ in range(word_count)]
    return " ".join(sentence)


# --- OS Functions ---
def resource_path(relative_path):
    """Return the absolute path to a bundled or local resource."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _win_set_clipboard_text(text):
    """Write text straight to the Windows clipboard using the raw Win32
    API (GlobalAlloc + SetClipboardData), bypassing Tk's own clipboard
    handling entirely. The moment SetClipboardData succeeds, Windows
    takes real ownership of that memory block -- unlike Tk's clipboard,
    which relies on the owning window still being alive to answer paste
    requests. That's why text copied this way survives after the app
    closes."""
    import ctypes
    from ctypes import wintypes

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # CRITICAL: without explicit argtypes/restype, ctypes assumes every
    # Win32 call returns a 32-bit int. GlobalAlloc/GlobalLock/SetClipboardData
    # all return pointer-sized (64-bit) handles on 64-bit Windows/Python, so
    # without these declarations the handle gets silently truncated to its
    # low 32 bits. OpenClipboard/EmptyClipboard/SetClipboardData still often
    # "succeed" (they return small BOOL/handle values), so no exception is
    # raised -- but GlobalLock/memmove end up touching the wrong address
    # whenever GlobalAlloc happens to return an address above 4GB (common
    # with ASLR), corrupting or losing the copied data. This is why it can
    # appear to work sometimes and fail other times.
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HANDLE
    kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HANDLE]
    kernel32.GlobalFree.restype = wintypes.HANDLE

    data = text.replace("\r\n", "\n").replace("\n", "\r\n") + "\0"
    encoded = data.encode("utf-16-le")

    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not h_mem:
            return False
        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            kernel32.GlobalFree(h_mem)
            return False
        ctypes.memmove(ptr, encoded, len(encoded))
        kernel32.GlobalUnlock(h_mem)
        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            kernel32.GlobalFree(h_mem)
            return False
    finally:
        user32.CloseClipboard()
    return True


# Every widget wired up via attach_clipboard_support() gets its own
# right-click context menu; this registry lets code elsewhere (e.g. the
# nav bar buttons) close whichever one happens to be open, without each
# caller needing a reference to that widget's specific menu.
_ALL_CONTEXT_MENUS = []


def close_all_context_menus():
    """Unpost every registered clipboard context menu, if any is open."""
    for menu in _ALL_CONTEXT_MENUS:
        try:
            menu.unpost()
        except Exception:
            pass


def attach_clipboard_support(widget):
    """Give a Text-like widget reliable Cut/Copy/Paste (copy survives
    the app closing, on Windows) plus a right-click context menu, since
    Tk text widgets don't provide one by default."""

    def get_selection():
        try:
            return widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return ""

    def do_copy(event=None):
        text = get_selection()
        if not text:
            return "break"
        ok = False
        if sys.platform.startswith("win"):
            try:
                ok = _win_set_clipboard_text(text)
            except Exception:
                ok = False
        if not ok:
            try:
                widget.clipboard_clear()
                widget.clipboard_append(text)
            except Exception:
                pass
        return "break"

    def do_cut(event=None):
        text = get_selection()
        if not text:
            return "break"
        do_copy()
        try:
            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return "break"

    def do_paste(event=None):
        try:
            text = widget.clipboard_get()
        except Exception:
            return "break"
        try:
            if widget.tag_ranges(tk.SEL):
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        widget.insert(tk.INSERT, text)
        return "break"

    def do_select_all(event=None):
        widget.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    widget.bind("<<Copy>>", do_copy)
    widget.bind("<Control-c>", do_copy)
    widget.bind("<Control-C>", do_copy)
    widget.bind("<<Cut>>", do_cut)
    widget.bind("<Control-x>", do_cut)
    widget.bind("<<Paste>>", do_paste)
    widget.bind("<Control-v>", do_paste)

    context_menu = tk.Menu(widget, tearoff=0)
    context_menu.add_command(label="Cut", command=do_cut)
    context_menu.add_command(label="Copy", command=do_copy)
    context_menu.add_command(label="Paste", command=do_paste)
    context_menu.add_separator()
    context_menu.add_command(label="Select All", command=do_select_all)
    _ALL_CONTEXT_MENUS.append(context_menu)

    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass

    widget.bind("<Button-3>", show_context_menu)


# --- English synonym lookup (used by "Synonym Translate") ---
# Uses a small precomputed table (synonyms.txt.gz) derived from WordNet,
# shipped next to this script/exe. No internet connection and no extra
# libraries (like nltk) are needed at runtime -- just the stdlib gzip module.
_SYNONYM_TABLE = None
_synonym_table_load_attempted = False


def _load_synonym_table():
    """Lazily load {WORD: [SYNONYM, ...]} from synonyms.txt.gz. Returns None
    if the file isn't available, so the rest of the app keeps working
    without the synonym-fallback feature."""
    global _SYNONYM_TABLE, _synonym_table_load_attempted

    if _synonym_table_load_attempted:
        return _SYNONYM_TABLE

    _synonym_table_load_attempted = True
    path = resource_path("synonyms.txt.gz")

    if not os.path.exists(path):
        return None

    try:
        table = {}
        with gzip.open(path, "rt", encoding="utf-8") as file_handle:
            for line in file_handle:
                line = line.rstrip("\n")
                if not line:
                    continue
                word, _, synonyms_part = line.partition("\t")
                table[word] = synonyms_part.split(",") if synonyms_part else []
        _SYNONYM_TABLE = table
    except Exception:
        _SYNONYM_TABLE = None

    return _SYNONYM_TABLE


def get_english_synonyms(word):
    """Return a list of single-word English synonyms for `word` (e.g.
    'DISPUTE' -> ['CONFLICT', 'QUARREL', ...]).
    Returns an empty list if the synonym table isn't available or the word
    isn't found."""
    table = _load_synonym_table()
    if table is None:
        return []
    return table.get(word.upper(), [])



def load_dict(filename):
    """Parse a Dwarf Fortress `language_*.txt` file for `[T_WORD:ENGLISH:fantasy]`
    entries and build four lookup tables: a canon English->fantasy dict
    (last entry in the file wins per word), an English->[all fantasy
    variants seen] dict, a canon fantasy->English dict (first entry seen
    wins), and a fantasy->[all English variants seen] dict. Returns
    (dictionary, reverse_dictionary, dictionary_all, reverse_dictionary_all);
    all four are empty if the file doesn't exist."""
    dictionary = {}
    dictionary_all = {}
    reverse_dictionary = {}
    reverse_dictionary_all = {}
    path = resource_path(filename)

    if os.path.exists(path):
        with open(path, "r", encoding="cp437", errors="ignore") as file_handle:
            for match in re.finditer(r"\[T_WORD:([^:]+):([^\]]+)\]", file_handle.read()):
                english_word = match.group(1).strip()
                fantasy_word = match.group(2).strip().lower()

                # Canon translation: last entry in the file wins (unchanged behavior).
                dictionary[english_word] = fantasy_word
                dictionary_all.setdefault(english_word, [])
                if fantasy_word not in dictionary_all[english_word]:
                    dictionary_all[english_word].append(fantasy_word)

                if fantasy_word not in reverse_dictionary:
                    reverse_dictionary[fantasy_word] = english_word.lower()
                reverse_dictionary_all.setdefault(fantasy_word, [])
                if english_word.lower() not in reverse_dictionary_all[fantasy_word]:
                    reverse_dictionary_all[fantasy_word].append(english_word.lower())

    return dictionary, reverse_dictionary, dictionary_all, reverse_dictionary_all


def load_all_dictionaries():
    """Call load_dict() for every language in LANGUAGE_FILES and collect the
    results into per-language dicts. Returns (dictionaries,
    reverse_dictionaries, dictionaries_all, reverse_dictionaries_all), each
    keyed by language name (e.g. "Dwarf")."""
    dictionaries = {}
    reverse_dictionaries = {}
    dictionaries_all = {}
    reverse_dictionaries_all = {}

    for language_name, filename in LANGUAGE_FILES.items():
        dictionary, reverse_dictionary, dictionary_all, reverse_dictionary_all = load_dict(filename)
        dictionaries[language_name] = dictionary
        reverse_dictionaries[language_name] = reverse_dictionary
        dictionaries_all[language_name] = dictionary_all
        reverse_dictionaries_all[language_name] = reverse_dictionary_all

    return dictionaries, reverse_dictionaries, dictionaries_all, reverse_dictionaries_all


def pick_synonym_value(candidates, canon_value):
    """Given every candidate translation seen for a word, return a random
    alternate one (a 'synonym') that differs from the canon value when
    possible, otherwise fall back to the canon value."""
    if not candidates:
        return canon_value

    unique_candidates = list(dict.fromkeys(candidates))
    alternates = [candidate for candidate in unique_candidates if candidate != canon_value]

    if not alternates:
        return canon_value

    return random.choice(alternates)


def center_window(window, width, height):
    """Resize `window` to `width` x `height` and reposition it so it's
    centered on the screen."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    center_x = int(screen_width / 2 - width / 2)
    center_y = int(screen_height / 2 - height / 2)
    window.geometry(f"{width}x{height}+{center_x}+{center_y}")


def english_candidates(word):
    """Given an uppercase English word, return it along with plausible
    de-inflected variants (stripping plural/-ed/-ing suffixes, e.g.
    "RUNNING" -> also try "RUNN"/"RUNNE") so dictionary lookups can match
    the base form even when the input is conjugated."""
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
    """Given a lowercase fantasy-language word, return it along with simple
    de-pluralized variants (stripping a trailing "es" or "s") so reverse
    dictionary lookups can still match the singular base form."""
    candidates = [word]

    if word.endswith("es") and len(word) > 2:
        candidates.append(word[:-2])
    if word.endswith("s") and len(word) > 1:
        candidates.append(word[:-1])

    return candidates


def strip_diacritics(text):
    """Return `text` with diacritical marks removed (e.g. "á" -> "a",
    "Kás" -> "Kas"), leaving the base Latin letters untouched. Used for
    diacritic-insensitive rhyme matching."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def find_rhyming_words(word, letter_count, reverse_dictionary_all, diacritic_sensitive=False):
    """Given a lowercase/mixed-case fantasy `word`, a rhyme depth
    `letter_count`, and a language's fantasy->[English words] reverse
    dictionary (as produced by load_dict/load_all_dictionaries), return a
    sorted list of every distinct fantasy word in that dictionary (other
    than `word` itself) whose last `letter_count` letters match the last
    `letter_count` letters of `word`. Words shorter than `letter_count`
    are skipped since they can't share a rhyme of that length.

    When `diacritic_sensitive` is False (the default), accented and
    unaccented letters are treated as equivalent for the comparison, so
    e.g. "Kás" rhymes with both "Kás" and "Kas". When True, accented and
    unaccented letters are only considered a match when they're
    identical, so "Kás" only rhymes with "Kás"."""
    normalized_word = word.strip().lower()
    if not normalized_word or letter_count < 1:
        return []

    suffix = normalized_word[-letter_count:]
    compare_suffix = suffix if diacritic_sensitive else strip_diacritics(suffix)
    matches = set()

    for candidate in reverse_dictionary_all:
        candidate_lower = candidate.lower()
        if candidate_lower == normalized_word:
            continue
        if len(candidate_lower) < letter_count:
            continue
        candidate_suffix = candidate_lower[-letter_count:]
        compare_candidate_suffix = candidate_suffix if diacritic_sensitive else strip_diacritics(candidate_suffix)
        if compare_candidate_suffix == compare_suffix:
            matches.add(candidate_lower)

    return sorted(matches)

# --- Autocomplete text ---

# Every AutoEntry/AutoText instance registers itself here so a single
# app-wide click handler (see close_all_autocomplete_popups, wired up
# in main() via root.bind_all) can close whichever instance's
# suggestion popup is open -- regardless of what got clicked (a nav
# button, a different output box, or even the same input box), since
# ordinary mouse clicks don't reliably move keyboard focus (Buttons in
# particular don't take focus on click, so <FocusOut> alone can't
# catch this).
_ALL_AUTOCOMPLETE_WIDGETS = []


def close_all_autocomplete_popups(event=None):
    """Close every open autocomplete suggestion popup, except one whose
    own listbox was just clicked (so picking a suggestion still works)."""
    clicked = event.widget if event is not None else None
    print(f"[DEBUG close_all_autocomplete_popups] event.widget={clicked!r}")
    for instance in _ALL_AUTOCOMPLETE_WIDGETS:
        if instance.popup and clicked is not instance.lb:
            instance.hide_popup()


class AutoEntry(tk.Entry):
    def __init__(self, master, get_d, get_mode_type, **kwargs):
        super().__init__(master, **kwargs)
        self.get_d = get_d
        self.get_mode_type = get_mode_type
        self.popup = None
        self.lb = None
        self.suppress_popup = False
        _ALL_AUTOCOMPLETE_WIDGETS.append(self)

        self.bind("<KeyRelease>", self.chk)
        self.bind("<Tab>", lambda event: self.sel() or "break")
        self.bind("<Return>", self.handle_return)
        self.bind("<Down>", self.focus_lb)
        self.bind("<Configure>", lambda event: self.hide_popup())
        self.bind("<Escape>", self.close_popup_event)

    def chk(self, event):
        if not self.winfo_exists():
            return

        if self.suppress_popup:
            if event.keysym in ("Escape", "Left", "Right", "Up", "Down", "Shift_L", "Shift_R"):
                return
            self.suppress_popup = False

        if event.keysym in ("Left", "Right", "Up", "Down", "Return", "Tab", "Shift_L", "Shift_R", "BackSpace"):
            if event.keysym == "BackSpace":
                current_text = self.get()
                cursor_pos = self.index(tk.INSERT)
                word_match = re.search(r"(\S+)\Z", current_text[:cursor_pos])
                if not word_match:
                    self.hide_popup()
                    return

        current_text = self.get()
        cursor_pos = self.index(tk.INSERT)
        word_match = re.search(r"(\S+)\Z", current_text[:cursor_pos])
        try:
            dictionary = self.get_d()
        except Exception:
            return

        mode_type = self.get_mode_type()
        if word_match and dictionary:
            prefix = unicodedata.normalize("NFC", word_match.group(1))
            # For the rhyme tab, fantasy keys are lowercase
            matches = [
                key for key in sorted(dictionary)
                if unicodedata.normalize("NFC", key).startswith(prefix.lower())
            ]
            print(
                f"[DEBUG AutoEntry.chk] keysym={event.keysym!r} char={event.char!r} "
                f"raw_prefix={word_match.group(1)!r} codepoints={[hex(ord(c)) for c in word_match.group(1)]} "
                f"mode={mode_type!r} matches={len(matches)}"
            )

            if matches:
                self.show_popup(matches, dictionary)
                return

        self.hide_popup()

    def show_popup(self, matches, dictionary):
        self.hide_popup()

        try:
            self.popup = tk.Toplevel(self)
            self.popup.wm_overrideredirect(True)

            # tk.Entry doesn't have bbox(), so we estimate popup placement below the entry field
            root_x = self.winfo_rootx()
            root_y = self.winfo_rooty() + self.winfo_height() + 2
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
                # Show key and its English translation(s) if available
                trans_val = ", ".join(dictionary.get(key, [])) if isinstance(dictionary.get(key), list) else dictionary.get(key, "")
                self.lb.insert(tk.END, f"{key} -> {trans_val}")

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
                    current_text = self.get()
                    cursor_pos = self.index(tk.INSERT)
                    word_match = re.search(r"(\S+)\Z", current_text[:cursor_pos])
                    if word_match:
                        start_idx = word_match.start(1)
                        self.delete(start_idx, cursor_pos)
                        self.insert(start_idx, key + " ")
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

class AutoText(scrolledtext.ScrolledText):

    def __init__(self, master, get_d, get_mode_type, **kwargs):
        """Set up a ScrolledText box with live autocomplete: `get_d` is a
        callback returning the dictionary to autocomplete against, and
        `get_mode_type` returns which translation direction is active (so
        matching can be case-normalized correctly). Wires up key bindings
        for triggering/dismissing the suggestion popup and for undo/redo."""
        kwargs.setdefault("undo", True)
        super().__init__(master, **kwargs)
        self.get_d = get_d
        self.get_mode_type = get_mode_type
        self.popup = None
        self.lb = None
        self.suppress_popup = False
        _ALL_AUTOCOMPLETE_WIDGETS.append(self)

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
        """Handle Ctrl+Z: undo the last text edit, ignoring the error Tk
        raises when the undo stack is empty."""
        try:
            self.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def redo_action(self, _event):
        """Handle Ctrl+Y / Ctrl+Shift+Z: redo the last undone text edit,
        ignoring the error Tk raises when the redo stack is empty."""
        try:
            self.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def chk(self, event):
        """Key-release handler that drives autocomplete: finds the word
        being typed at the cursor, looks it up (prefix match) against the
        active dictionary in the correct case for the current translation
        direction, and shows or hides the suggestion popup accordingly.
        Also handles dismissing the popup on navigation/Backspace keys."""
        if not self.winfo_exists():
            return

        if self.suppress_popup:
            if event.keysym in ("Escape", "Left", "Right", "Up", "Down", "Shift_L", "Shift_R"):
                return
            self.suppress_popup = False

        if event.keysym in ("Left", "Right", "Up", "Down", "Return", "Tab", "Shift_L", "Shift_R", "BackSpace"):
            if event.keysym == "BackSpace":
                word_match = re.search(r"(\S+)\Z", self.get("1.0", tk.INSERT))
                if not word_match:
                    self.hide_popup()
                    return

        word_match = re.search(r"(\S+)\Z", self.get("1.0", tk.INSERT))
        try:
            dictionary = self.get_d()
        except Exception:
            return

        mode_type = self.get_mode_type()
        if word_match and dictionary:
            prefix = unicodedata.normalize("NFC", word_match.group(1))
            if mode_type == "eng_to_fan":
                matches = [
                    key for key in sorted(dictionary)
                    if unicodedata.normalize("NFC", key).startswith(prefix.upper())
                ]
            else:
                matches = [
                    key for key in sorted(dictionary)
                    if unicodedata.normalize("NFC", key).startswith(prefix.lower())
                ]
            print(
                f"[DEBUG AutoText.chk] keysym={event.keysym!r} char={event.char!r} "
                f"raw_prefix={word_match.group(1)!r} codepoints={[hex(ord(c)) for c in word_match.group(1)]} "
                f"mode={mode_type!r} matches={len(matches)}"
            )

            if matches:
                self.show_popup(matches, dictionary)
                return

        self.hide_popup()

    def show_popup(self, matches, dictionary):
        """Display a borderless Toplevel positioned just below the text
        cursor, containing a Listbox of `matches` (each shown as
        "key -> translation") for the user to pick from with Tab/Enter/click."""
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
        """Destroy the autocomplete suggestion popup, if one is showing, and
        clear the stored popup/listbox references."""
        if self.popup:
            import traceback
            print("[DEBUG AutoText.hide_popup] called from:")
            traceback.print_stack(limit=4)
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
            self.lb = None

    def focus_lb(self, _event):
        """Handle the Down key: move keyboard focus into the suggestion
        listbox (if the popup is open) and select its first item."""
        if self.lb:
            try:
                self.lb.focus_set()
                self.lb.selection_set(0)
            except Exception:
                pass
            return "break"

    def sel(self):
        """Accept the currently selected suggestion: replace the in-progress
        word at the cursor with the chosen dictionary key plus a trailing
        space, then close the popup and return focus to the text box."""
        if self.lb:
            try:
                selection = self.lb.curselection()
                if selection:
                    key = self.lb.get(selection[0]).split(" -> ")[0]
                    word_match = re.search(r"(\S+)\Z", self.get("1.0", tk.INSERT))
                    if word_match:
                        self.delete(f"insert-{len(word_match.group(1))}c", tk.INSERT)
                        self.insert(tk.INSERT, key + " ")
            except Exception:
                pass
            self.hide_popup()
            self.focus_set()
            return "break"

    def handle_return(self, _event):
        """Enter-key handler for the text box itself; intentionally a no-op
        so Enter still inserts a normal newline (suggestion acceptance on
        Enter is instead handled by the listbox's own binding in
        show_popup)."""
        return None

    def close_popup_event(self, _event):
        """Handle Escape: close the suggestion popup and briefly suppress
        it from reopening on the same keystroke, so Escape doesn't
        immediately retrigger the popup via chk()."""
        if self.popup:
            self.suppress_popup = True
            self.hide_popup()
            return "break"
        return None


def _match_english_word_in_dict(upper_word, target_dict):
    """Try an English word (already uppercased) against target_dict, including
    its inflected-suffix variants (e.g. plurals, -ed, -ing). Returns
    (translation, matched_key) or (None, None)."""
    if upper_word in target_dict:
        return target_dict[upper_word], upper_word
    for candidate in english_candidates(upper_word):
        if candidate in target_dict:
            return target_dict[candidate], candidate
    return None, None


def lookup_single(
    token,
    target_dict,
    source_reverse_dict,
    mode_type,
    target_dict_all=None,
    source_reverse_dict_all=None,
    use_synonyms=False,
    apply_case=True,
):
    """Translate a single `token` for the given `mode_type`
    ("eng_to_fan", "fan_to_eng", or "fan_to_fan"), trying an exact match
    first and falling back to inflected-form variants (via
    english_candidates/fantasy_candidates). When `use_synonyms` is True,
    substitutes a random alternate translation (via pick_synonym_value) and,
    for untranslated English input, also tries real English synonyms of the
    word. Restores the original word's capitalization/uppercase pattern
    when `apply_case` is True. Returns the translated string, or None if no
    match was found."""
    is_capitalized = token.istitle()
    is_upper = token.isupper()

    result = None
    if mode_type == "eng_to_fan":
        upper_token = token.upper()
        result, matched_key = _match_english_word_in_dict(upper_token, target_dict)

        if use_synonyms:
            if matched_key:
                if target_dict_all:
                    result = pick_synonym_value(target_dict_all.get(matched_key), result)
            else:
                # The word itself has no dictionary entry at all. Try real
                # English synonyms of it (e.g. "dispute" -> "conflict") and
                # translate the first one that IS in the dictionary.
                for synonym in get_english_synonyms(token):
                    result, matched_key = _match_english_word_in_dict(synonym.upper(), target_dict)
                    if result:
                        break
                if matched_key and target_dict_all:
                    result = pick_synonym_value(target_dict_all.get(matched_key), result)
    elif mode_type == "fan_to_eng":
        lower_token = token.lower()
        matched_key = None
        if lower_token in source_reverse_dict:
            result = source_reverse_dict[lower_token]
            matched_key = lower_token
        else:
            for candidate in fantasy_candidates(lower_token):
                if candidate in source_reverse_dict:
                    result = source_reverse_dict[candidate]
                    matched_key = candidate
                    break
        if use_synonyms and matched_key and source_reverse_dict_all:
            result = pick_synonym_value(source_reverse_dict_all.get(matched_key), result)
    else:
        lower_token = token.lower()
        english_word = None
        matched_fan_key = None
        for candidate in fantasy_candidates(lower_token):
            if candidate in source_reverse_dict:
                english_word = source_reverse_dict[candidate]
                matched_fan_key = candidate
                break
        if use_synonyms and matched_fan_key and source_reverse_dict_all:
            english_word = pick_synonym_value(source_reverse_dict_all.get(matched_fan_key), english_word)
        if english_word:
            result, matched_eng_key = _match_english_word_in_dict(english_word.upper(), target_dict)

            if use_synonyms:
                if matched_eng_key:
                    if target_dict_all:
                        result = pick_synonym_value(target_dict_all.get(matched_eng_key), result)
                else:
                    for synonym in get_english_synonyms(english_word):
                        result, matched_eng_key = _match_english_word_in_dict(synonym.upper(), target_dict)
                        if result:
                            break
                    if matched_eng_key and target_dict_all:
                        result = pick_synonym_value(target_dict_all.get(matched_eng_key), result)

    if result and apply_case:
        if is_upper:
            return result.upper()
        elif is_capitalized:
            return result.capitalize()
    return result


def translate_word(
    token,
    target_dict,
    source_reverse_dict,
    mode_type,
    target_dict_all=None,
    source_reverse_dict_all=None,
    use_synonyms=False,
):
    """Translate `token` as a whole word via lookup_single(); if that fails,
    fall back to splitting the token into a left/right substring pair at
    every possible position and translating each half independently
    (a crude compound-word heuristic), returning the first combination
    where both halves translate. Returns None if nothing matches at all."""
    direct_translation = lookup_single(
        token, target_dict, source_reverse_dict, mode_type, target_dict_all, source_reverse_dict_all, use_synonyms
    )
    if direct_translation:
        return direct_translation

    is_capitalized = token.istitle()
    is_upper = token.isupper()

    base_token = token.upper() if mode_type == "eng_to_fan" else token.lower()
    for index in range(2, len(base_token) - 1):
        left_part = base_token[:index]
        right_part = base_token[index:]
        left_translation = lookup_single(
            left_part, target_dict, source_reverse_dict, mode_type, target_dict_all, source_reverse_dict_all,
            use_synonyms, apply_case=False
        )
        if not left_translation:
            continue

        right_translation = lookup_single(
            right_part, target_dict, source_reverse_dict, mode_type, target_dict_all, source_reverse_dict_all,
            use_synonyms, apply_case=False
        )
        if not right_translation:
            continue

        combined = left_translation + right_translation
        if is_upper:
            return combined.upper()
        elif is_capitalized:
            return combined.capitalize()
        return combined

    return None



# ###############################################################################################################
# ########################################## MAIN FUNCTION ######################################################
# ###############################################################################################################
def main():
    """Entry point: load all language dictionaries, build the entire Tk GUI
    (nav bar, the Canon/Relaxed translation tabs, the Kobold and Divine
    gibberish-generator tabs), wire up all event handlers, and start the Tk
    main loop."""
    dicts, rev_dicts, dicts_all, rev_dicts_all = load_all_dictionaries()

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_GEOMETRY)
    center_window(root, WINDOW_WIDTH, WINDOW_HEIGHT)
    root.resizable(True, True)

    # Close any open autocomplete suggestion popup on ANY click anywhere
    # in the app -- a nav button, a different box, or even the same
    # input box the popup belongs to. A per-widget FocusOut isn't
    # enough: ordinary Buttons don't take keyboard focus on click, and
    # clicking inside the same box that already has focus never fires
    # FocusOut at all.
    root.bind_all("<Button-1>", close_all_autocomplete_popups, add="+")

    try:
        root.iconbitmap(resource_path("df_codexlogo.ico"))
    except Exception:
        pass

    def _persist_clipboard_linux():
        """On X11/Wayland, whichever app owns the clipboard must stay
        running to serve paste requests -- there's no OS-level flush like
        Windows has. So we hand the current clipboard text off to a
        small external helper (xclip / xsel / wl-copy) that keeps running
        as its own process after we exit, the same trick clipboard
        managers use."""
        try:
            text = root.clipboard_get()
        except Exception:
            return  # nothing was copied

        import subprocess
        import shutil

        candidates = [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]
        for cmd in candidates:
            if shutil.which(cmd[0]):
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        close_fds=True,
                        start_new_session=True,
                    )
                    proc.communicate(text.encode("utf-8"), timeout=2)
                except Exception:
                    pass
                return

    def on_closing():
        """Window-close handler: before the app exits, force the OS to take
        ownership of any clipboard text the user copied (OleFlushClipboard
        on Windows, an external persist helper on Linux) so it survives
        after the process ends, then tear down the Tk root."""
        try:
            if sys.platform.startswith("win"):
                # Tkinter uses "delayed rendering" for the clipboard: it
                # doesn't hand the copied text over to Windows until
                # another app requests it. If our process exits first,
                # the text is lost. OleFlushClipboard forces Windows to
                # take a permanent copy of the clipboard right now.
                try:
                    import ctypes
                    # OleFlushClipboard is part of the OLE/COM subsystem.
                    # It requires the calling thread to have initialized
                    # OLE first, or it fails silently with
                    # CO_E_NOTINITIALIZED. Tkinter never calls this on its
                    # own, so we have to do it ourselves before flushing.
                    ctypes.windll.ole32.OleInitialize(None)
                    ctypes.oledll.ole32.OleFlushClipboard()
                except Exception:
                    pass
            elif sys.platform.startswith("linux"):
                _persist_clipboard_linux()
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # --- Top Navigation Bar for Switching Interfaces (Placed First) ---
    nav_bar = tk.Frame(root, bg="#e0e0e0", height=34)
    nav_bar.pack(side=tk.TOP, fill=tk.X)

    NAV_BTN_DEFAULT_BG = nav_bar.cget("bg")
    NAV_BTN_ACTIVE_BG = "#A9A9A9"
    NAV_BTN_ACTIVE_FG = "white"

    nav_buttons = []

    def set_active_nav_button(active_button):
        """Visually highlight `active_button` (sunken, gray, white text) in
        the top nav bar and reset all other nav buttons to their default
        raised appearance."""
        for button in nav_buttons:
            if button is active_button:
                button.config(relief=tk.SUNKEN, bg=NAV_BTN_ACTIVE_BG, fg=NAV_BTN_ACTIVE_FG)
            else:
                button.config(relief=tk.RAISED, bg=NAV_BTN_DEFAULT_BG, fg="black")

    def switch_to(frame, button):
        """Switch the main content area to `frame` and mark `button` as the
        active nav button."""
        close_all_context_menus()
        show_frame(frame)
        set_active_nav_button(button)

    NAV_BTN_FONT = ("Arial", 12, "bold")
    NAV_BTN_WIDTH = 8
    NAV_BTN_PADX = 4
    NAV_BTN_PADY = 3

    btn_dictionary = tk.Button(
        nav_bar,
        text="Dictionary",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_dictionary.config(command=lambda: switch_to(dictionary_frame, btn_dictionary))
    btn_dictionary.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_dictionary)

    btn_translations = tk.Button(
        nav_bar,
        text="Canon",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_translations.config(command=lambda: switch_to(trans_frame, btn_translations))
    btn_translations.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_translations)

    btn_synonyms = tk.Button(
        nav_bar,
        text="Relaxed",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_synonyms.config(command=lambda: switch_to(synonym_frame, btn_synonyms))
    btn_synonyms.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_synonyms)

    btn_kobol = tk.Button(
        nav_bar,
        text="Kobold",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_kobol.config(command=lambda: switch_to(kobold_frame, btn_kobol))
    btn_kobol.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_kobol)

    btn_divine = tk.Button(
        nav_bar,
        text="Divine",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_divine.config(command=lambda: switch_to(divine_frame, btn_divine))
    btn_divine.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_divine)

    btn_rhyme = tk.Button(
        nav_bar,
        text="Rhymes",
        font=NAV_BTN_FONT,
        width=NAV_BTN_WIDTH,
    )
    btn_rhyme.config(command=lambda: switch_to(rhyme_frame, btn_rhyme))
    btn_rhyme.pack(side=tk.LEFT, padx=NAV_BTN_PADX, pady=NAV_BTN_PADY)
    nav_buttons.append(btn_rhyme)

    # --- Container for Main Content Frames ---
    container = tk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True)

    dictionary_frame = tk.Frame(container)
    trans_frame = tk.Frame(container)
    kobold_frame = tk.Frame(container)
    divine_frame = tk.Frame(container)
    synonym_frame = tk.Frame(container)
    rhyme_frame = tk.Frame(container)

    for frame in (dictionary_frame, trans_frame, kobold_frame, divine_frame, synonym_frame, rhyme_frame):
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    active_frame = {"current": None}

    def show_frame(frame):
        """Raise `frame` to the top of the stack of overlapping tab frames,
        making it the visible one, and remember it as the active frame so
        tab-scoped global shortcuts (like Ctrl+F) know where to act."""
        active_frame["current"] = frame
        frame.tkraise()

    def add_write_me_button(parent_frame):
        """Add a "Facing an issue? Write me!" link-style button to the
        bottom of `parent_frame` that opens a small support-contact dialog."""
        def show_email_dialog():
            """Open a small modal Toplevel showing a read-only support
            contact email address, with a Close button."""
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
            parent_frame,
            text="Facing an issue? Write me!",
            command=show_email_dialog,
            font=("Arial", 9),
            fg="red",
            cursor="hand2",
        ).pack(side=tk.BOTTOM, pady=(0, 10))

    # ==================== DICTIONARY INTERFACE ====================
    def build_dictionary_tab(parent_frame):
        """Build a read-only, scrollable table listing every English word
        alongside its Dwarf/Elf/Human/Goblin translations, one row per
        word, side by side in five columns."""
        tk.Label(
            parent_frame,
            text="Dictionary",
            font=("Arial", 12, "bold"),
        ).pack(pady=15)

        search_frame = tk.Frame(parent_frame)
        search_frame.pack(fill=tk.X, padx=15, pady=(0, 2))

        tk.Label(search_frame, text="Search:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar(parent_frame)
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        attach_clipboard_support(search_entry)

        match_label = tk.Label(search_frame, text="", font=("Arial", 9), fg="#666666")
        match_label.pack(side=tk.LEFT, padx=(8, 8))

        tk.Button(
            search_frame,
            text="✕",
            width=2,
            command=lambda: search_var.set(""),
        ).pack(side=tk.LEFT)

        # --- Special Character Buttons Frame for the search box ---
        dict_chars_frame = tk.Frame(parent_frame)
        dict_chars_frame.pack(fill=tk.X, padx=15, pady=2)

        def insert_dict_char(char):
            """Insert `char` (a special accented character) at the cursor
            in the search box, keep focus there, and re-fire the filter
            (the textvariable trace already does this, but focusing
            afterward lets the user keep typing right away)."""
            search_entry.insert(tk.INSERT, char)
            search_entry.focus_set()

        def relayout_dict_chars(event=None):
            """Rebuild the grid of special-character buttons to fit the
            current width of `dict_chars_frame`, wrapping to as many
            columns as fit (called on frame resize)."""
            for widget in dict_chars_frame.winfo_children():
                widget.destroy()

            frame_width = dict_chars_frame.winfo_width()
            if frame_width < 10:
                frame_width = 450

            btn_width_px = 24
            columns = max(1, frame_width // btn_width_px)

            for index, character in enumerate(SPECIAL_CHARACTERS):
                row_index = index // columns
                col_index = index % columns
                button = tk.Button(
                    dict_chars_frame,
                    text=character,
                    width=2,
                    font=("Arial", 8),
                    command=lambda current_char=character: insert_dict_char(current_char),
                )
                button.grid(row=row_index, column=col_index, padx=1, pady=1)

        dict_chars_frame.bind("<Configure>", relayout_dict_chars)

        for index, character in enumerate(SPECIAL_CHARACTERS):
            row_index = index // 19
            col_index = index % 19
            button = tk.Button(
                dict_chars_frame,
                text=character,
                width=2,
                font=("Arial", 8),
                command=lambda current_char=character: insert_dict_char(current_char),
            )
            button.grid(row=row_index, column=col_index, padx=1, pady=1)

        table_frame = tk.Frame(parent_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        columns = ("English", "Dwarf", "Elf", "Human", "Goblin")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Tracks which column is currently sorted and in which direction, so
        # clicking the same header again reverses the order (like Excel).
        sort_state = {"column": None, "reverse": False}

        def apply_current_sort():
            """Re-apply whatever sort is currently active (if any) to
            whatever rows are presently shown in `tree` -- used both when a
            header is clicked and after the search filter changes what's
            displayed, so sorting and searching stay consistent together."""
            column_name = sort_state["column"]
            if not column_name:
                return
            rows = [(tree.set(item_id, column_name), item_id) for item_id in tree.get_children("")]
            rows.sort(key=lambda row: row[0].lower(), reverse=sort_state["reverse"])
            for sort_index, (_value, item_id) in enumerate(rows):
                tree.move(item_id, "", sort_index)

        def sort_by_column(column_name):
            """Re-sort every row in `tree` by the text in `column_name`
            (case-insensitive), toggling ascending/descending if that same
            column was just clicked, and refresh the header labels with a
            ▲/▼ arrow marking the active sort."""
            if sort_state["column"] == column_name:
                sort_state["reverse"] = not sort_state["reverse"]
            else:
                sort_state["column"] = column_name
                sort_state["reverse"] = False

            apply_current_sort()

            for other_column in columns:
                arrow = ""
                if other_column == column_name:
                    arrow = " ▼" if sort_state["reverse"] else " ▲"
                tree.heading(other_column, text=other_column + arrow)

        for column_name in columns:
            tree.heading(column_name, text=column_name, command=lambda c=column_name: sort_by_column(c))
            tree.column(column_name, anchor="w", width=110, stretch=True)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=v_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Every English word that appears in any of the four language
        # dictionaries, so the table stays complete even if one file is
        # missing a word another one has. Kept around (separately from
        # whatever's currently in `tree`) so the search box can filter it
        # without losing the un-filtered data.
        all_english_words = set()
        for language_dict in dicts.values():
            all_english_words.update(language_dict.keys())

        all_rows = []
        for english_word in sorted(all_english_words):
            row_values = [english_word.capitalize()]
            for language_name in ("Dwarf", "Elf", "Human", "Goblin"):
                row_values.append(dicts.get(language_name, {}).get(english_word, ""))
            all_rows.append(tuple(row_values))

        def populate_tree(rows):
            """Clear `tree` and refill it with exactly `rows`."""
            tree.delete(*tree.get_children(""))
            for row in rows:
                tree.insert("", tk.END, values=row)

        def apply_search(*_args):
            """Filter the table to rows where the search text appears
            (case-insensitively) in ANY of the five columns -- English or
            any language's translation -- re-applying the active sort
            afterward, and show a small match count next to the box."""
            query = search_var.get().strip().lower()
            if query:
                filtered_rows = [
                    row for row in all_rows
                    if any(query in str(value).lower() for value in row)
                ]
            else:
                filtered_rows = all_rows

            populate_tree(filtered_rows)
            apply_current_sort()

            if query:
                count = len(filtered_rows)
                match_label.config(text=f"{count} match{'es' if count != 1 else ''}")
            else:
                match_label.config(text="")

        search_var.trace_add("write", apply_search)
        populate_tree(all_rows)

        def focus_search(_event=None):
            """Ctrl+F handler: jump focus to the search box and select its
            current contents, but only while the Dictionary tab is the one
            actually on screen, so Ctrl+F on other tabs isn't hijacked."""
            if active_frame.get("current") is parent_frame:
                search_entry.focus_set()
                search_entry.selection_range(0, tk.END)
                return "break"
            return None

        root.bind_all("<Control-f>", focus_search, add="+")
        root.bind_all("<Control-F>", focus_search, add="+")

        def clear_search_and_defocus(_event=None):
            """Escape handler for the search box: clear the search and
            hand focus back to the table."""
            search_var.set("")
            tree.focus_set()
            return "break"

        search_entry.bind("<Escape>", clear_search_and_defocus)
        search_entry.bind("<Return>", lambda _event: (tree.focus_set(), "break")[1])

    def build_translation_tab(parent_frame, use_synonyms):
        """Build one full translation tab's UI and logic inside
        `parent_frame` (used for both the "Canon" and "Relaxed"/synonym
        tabs, distinguished by `use_synonyms`): language pickers, the
        special-character bar, input/output text boxes, and the
        translate/swap button behavior."""
        in_lang_var = tk.StringVar(parent_frame, "English")
        out_lang_var = tk.StringVar(parent_frame, "Dwarf")

        def get_mode_type():
            """Derive the current translation direction from the selected
            input/output languages: "eng_to_fan", "fan_to_eng", or
            "fan_to_fan" (used when neither side is English, i.e.
            fantasy-to-fantasy via English as a pivot)."""
            input_language = in_lang_var.get()
            output_language = out_lang_var.get()
            if input_language == "English" and output_language != "English":
                return "eng_to_fan"
            if input_language != "English" and output_language == "English":
                return "fan_to_eng"
            return "fan_to_fan"

        def get_active_dicts():
            """Return the (target_dict, source_reverse_dict) pair
            appropriate for the current mode_type/language selection, for
            use by translate_word/lookup_single."""
            input_language = in_lang_var.get()
            output_language = out_lang_var.get()
            mode_type = get_mode_type()

            if mode_type == "eng_to_fan":
                return dicts[output_language], None
            if mode_type == "fan_to_eng":
                return None, rev_dicts[input_language]
            return dicts[output_language], rev_dicts[input_language]

        def get_active_dicts_all():
            """Like get_active_dicts(), but returns the "_all" variants
            (every translation seen per word) needed for synonym
            selection."""
            input_language = in_lang_var.get()
            output_language = out_lang_var.get()
            mode_type = get_mode_type()

            if mode_type == "eng_to_fan":
                return dicts_all[output_language], None
            if mode_type == "fan_to_eng":
                return None, rev_dicts_all[input_language]
            return dicts_all[output_language], rev_dicts_all[input_language]

        def update_labels():
            """Refresh the "Input (...)"/"Output (...)" labels to reflect
            the currently selected languages."""
            in_label.config(text=f"Input ({in_lang_var.get()}):")
            out_label.config(text=f"Output ({out_lang_var.get()}):")

        def get_phrase_dictionary(mode_type, target_dict, source_reverse_dict):
            """Pick which dictionary to scan for multi-word phrase entries
            (keys containing a space), based on translation direction."""
            if mode_type == "eng_to_fan":
                return target_dict
            return source_reverse_dict

        def translate_phrase_matches_with_map(line, phrase_dict):
            """Replace every multi-word phrase key found in `phrase_dict`
            (longest phrases first, case-insensitive) within `line` with its
            translated value, before word-by-word translation runs.

            Because a phrase substitution can change the text's length
            (e.g. "PASS VERB" -> "adas"), the resulting `working_line` is
            no longer character-aligned with the original `line`. To let
            callers still highlight positions in the ORIGINAL line
            correctly, this also returns `char_map`: a list the same
            length as `working_line`, where `char_map[i]` is either the
            index of the corresponding character in the original `line`,
            or None if that character came from a phrase's translated
            value (and therefore has no single corresponding position in
            the original, untranslated text)."""
            # Each segment tracks a chunk of `working_line`'s text together
            # with the (start, end) span it occupies in the ORIGINAL line,
            # or (None, None) if it's substituted/translated text.
            segments = [{"text": line, "start": 0, "end": len(line)}]
            phrase_keys = sorted((key for key in phrase_dict if " " in key), key=len, reverse=True)

            for phrase_key in phrase_keys:
                translated_value = phrase_dict.get(phrase_key)
                pattern = re.compile(re.escape(phrase_key), re.IGNORECASE)
                new_segments = []
                for seg in segments:
                    text, start = seg["text"], seg["start"]
                    last_end = 0
                    for m in pattern.finditer(text):
                        if m.start() > last_end:
                            pre_text = text[last_end:m.start()]
                            pre_start = None if start is None else start + last_end
                            pre_end = None if start is None else start + m.start()
                            new_segments.append({"text": pre_text, "start": pre_start, "end": pre_end})
                        new_segments.append({"text": translated_value, "start": None, "end": None})
                        last_end = m.end()
                    if last_end < len(text):
                        trail_text = text[last_end:]
                        trail_start = None if start is None else start + last_end
                        trail_end = None if start is None else start + len(text)
                        new_segments.append({"text": trail_text, "start": trail_start, "end": trail_end})
                segments = new_segments

            working_line = "".join(seg["text"] for seg in segments)
            char_map = []
            for seg in segments:
                if seg["start"] is None:
                    char_map.extend([None] * len(seg["text"]))
                else:
                    char_map.extend(range(seg["start"], seg["end"]))
            return working_line, char_map

        def map_to_original_range(char_map, start_col, end_col):
            """Translate a [start_col, end_col) column range in a
            phrase-substituted `working_line` back into the matching
            [orig_start, orig_end) range in the original line, using the
            `char_map` produced by translate_phrase_matches_with_map().
            Returns None if the range isn't a contiguous chunk of
            untouched original text (e.g. it falls inside, or spans into,
            a phrase's substituted translation) -- in that case there is
            no single correct span in the original text to highlight."""
            sub_map = char_map[start_col:end_col]
            if not sub_map or any(index is None for index in sub_map):
                return None
            if sub_map != list(range(sub_map[0], sub_map[0] + len(sub_map))):
                return None
            return sub_map[0], sub_map[-1] + 1

        all_known_words = set()
        for language_dict in dicts.values():
            for english_word, fantasy_word in language_dict.items():
                all_known_words.add(english_word.lower())
                all_known_words.add(fantasy_word.lower())

        def is_known_allowed_word(token, target_dict, source_reverse_dict):
            """Return True if `token` (not itself a stop word) already
            appears as a key or value in the dictionary/reverse-dictionary
            pair that's actually active for the current translation
            direction, meaning it's fine to leave untranslated/pass through
            as-is rather than flagging it as unrecognized. (Scoped to the
            active pair only -- checking every language's dictionaries here
            for ALL words caused unrelated lowercase words from other
            fantasy languages to be waved through unchanged instead of
            being translated or flagged.)

            Only reached after translate_word() has already had a chance to
            translate `token`, so an ordinary capitalized English word that
            DOES have a real translation still gets translated normally --
            this is purely a fallback for tokens translation couldn't
            handle. As an extra fallback (proper-name rule), a capitalized
            token that appears anywhere across ALL FOUR language
            dictionaries -- not just the active pair -- is treated as a
            name (e.g. "Urist") and passed through unchanged, regardless of
            which languages are currently selected."""
            token_lower = token.lower()
            if token_lower in STOP_WORDS:
                return False

            for dictionary in (target_dict, source_reverse_dict):
                if not dictionary:
                    continue
                if token_lower in dictionary or token_lower in dictionary.values():
                    return True

            if (token.istitle() or token.isupper()) and token_lower in all_known_words:
                return True

            return False

        def trans(*_args):
            """Main translate action: read the input box line by line,
            apply phrase-level translation then per-token translation
            (skipping stop words), highlight any token that couldn't be
            translated and isn't otherwise a recognized word, and write the
            joined result into the output box."""
            try:
                if not root.winfo_exists() or not out_box.winfo_exists():
                    return
            except Exception:
                return

            in_box.tag_remove("untranslated", "1.0", tk.END)

            mode_type = get_mode_type()
            target_dict, source_reverse_dict = get_active_dicts()
            target_dict_all, source_reverse_dict_all = get_active_dicts_all()
            phrase_dict = get_phrase_dictionary(mode_type, target_dict, source_reverse_dict)
            input_text = in_box.get("1.0", tk.END)
            translated_lines = []

            for line_index, line in enumerate(input_text.splitlines(), start=1):
                working_line, char_map = translate_phrase_matches_with_map(line, phrase_dict)
                translated_words = []

                for match in re.finditer(r"\b\w+\b|[^\s\w]", working_line):
                    token = match.group(0)
                    start_col = match.start()
                    end_col = match.end()

                    # Positions are found in `working_line` (post phrase
                    # substitution), but highlighting must land on the
                    # ORIGINAL text the user typed. Map back through
                    # char_map; tokens that fall inside a phrase's
                    # substituted translation (e.g. "adas" from "PASS
                    # VERB") have no corresponding original span, so they
                    # should never be tagged.
                    orig_range = map_to_original_range(char_map, start_col, end_col)

                    if token.lower() in STOP_WORDS:
                        if orig_range:
                            orig_start, orig_end = orig_range
                            in_box.tag_add("untranslated", f"{line_index}.{orig_start}", f"{line_index}.{orig_end}")
                        continue

                    translated_word = translate_word(
                        token,
                        target_dict,
                        source_reverse_dict,
                        mode_type,
                        target_dict_all,
                        source_reverse_dict_all,
                        use_synonyms,
                    )

                    if translated_word:
                        translated_words.append(translated_word)
                        continue

                    if is_known_allowed_word(token, target_dict, source_reverse_dict):
                        translated_words.append(token)
                        continue

                    if orig_range:
                        orig_start, orig_end = orig_range
                        in_box.tag_add("untranslated", f"{line_index}.{orig_start}", f"{line_index}.{orig_end}")

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
            """Respond to the input-language dropdown changing: revert the
            change if it would collide with the output language, confirm
            with the user before clearing existing text (since switching
            languages invalidates it), then update labels and re-translate."""
            nonlocal last_in_lang, is_reverting
            if is_reverting:
                return

            current_input = in_lang_var.get()
            if current_input == out_lang_var.get():
                messagebox.showwarning(
                    "Same language selected",
                    "Input and output can't both be "
                    f"\"{current_input}\". Reverting to the previous "
                    "input language.",
                    parent=parent_frame,
                )
                is_reverting = True
                in_lang_var.set(last_in_lang)
                is_reverting = False
                return

            if current_input != last_in_lang:
                has_content = bool(
                    in_box.get("1.0", tk.END).strip()
                    or out_box.get("1.0", tk.END).strip()
                )
                if has_content:
                    confirmed = messagebox.askyesno(
                        "Reset input and output?",
                        "Changing the input language will clear the current "
                        "input and output text.\n\nDo you really want to "
                        "reset input and output?",
                        parent=parent_frame,
                    )
                    if not confirmed:
                        is_reverting = True
                        in_lang_var.set(last_in_lang)
                        is_reverting = False
                        return

                last_in_lang = current_input
                in_box.delete("1.0", tk.END)
                out_box.delete("1.0", tk.END)

            update_labels()
            trans()

        def on_out_lang_change(*_args):
            """Respond to the output-language dropdown changing: revert the
            change if it would collide with the input language, otherwise
            update labels and re-translate (output language changes don't
            clear existing text)."""
            nonlocal last_out_lang, is_reverting
            if is_reverting:
                return

            current_output = out_lang_var.get()
            if current_output == in_lang_var.get():
                messagebox.showwarning(
                    "Same language selected",
                    "Input and output can't both be "
                    f"\"{current_output}\". Reverting to the previous "
                    "output language.",
                    parent=parent_frame,
                )
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
            """Replace `text_box`'s contents with `text`, trimmed of
            surrounding whitespace (re-adding a single trailing newline if
            non-empty)."""
            stripped_text = text.strip()
            text_box.delete("1.0", tk.END)
            text_box.insert("1.0", stripped_text + ("\n" if stripped_text else ""))

        def swap_languages_and_content():
            """Handle the "⇄" button: swap the selected input/output
            languages and swap the input/output box contents to match,
            then re-translate."""
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

        tab_title = "Relaxed Translation \n (Uses synonyms, may be misleading)" if use_synonyms else "Canon Translation \n (Official translation 1 to 1)"
        tk.Label(
            parent_frame,
            text=tab_title,
            font=("Arial", 12, "bold"),
        ).pack(pady=15)

        top_frame = tk.Frame(parent_frame)
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

        in_label = tk.Label(parent_frame, text="Input (English):", font=("Arial", 10, "bold"))
        in_label.pack(anchor="w", padx=15)

        chars_frame = tk.Button(parent_frame)  # or standard tk.Frame
        chars_frame = tk.Frame(parent_frame)
        chars_frame.pack(fill=tk.X, padx=15, pady=2)

        def insert_char(char):
            """Insert `char` (a special accented character) at the cursor in
            the input box and return focus to it."""
            print(f"[DEBUG insert_char] inserting {char!r} codepoints={[hex(ord(c)) for c in char]}")
            in_box.insert(tk.INSERT, char)
            in_box.focus_set()
            # Clicking this button (like any click) triggers the app-wide
            # popup-close handler before this command runs, so force the
            # autocomplete popup to recompute/reopen against the text we
            # just inserted -- otherwise it stays closed until the next
            # real keystroke.
            in_box.event_generate("<KeyRelease>")
            print("[DEBUG insert_char] done, popup is now:", in_box.popup)

        def relayout_chars(event=None):
            """Rebuild the grid of special-character buttons to fit the
            current width of `chars_frame`, wrapping to as many columns as
            fit (called on frame resize)."""
            # Clear existing buttons
            for widget in chars_frame.winfo_children():
                widget.destroy()

            # Get current frame width, default to a minimum if not yet rendered
            frame_width = chars_frame.winfo_width()
            if frame_width < 10:
                frame_width = 450

            btn_width_px = 24
            columns = max(1, frame_width // btn_width_px)

            # Do NOT add weights to columns so they don't artificially stretch apart.
            # Instead, create an inner sub-container or let them pack naturally.

            for index, character in enumerate(SPECIAL_CHARACTERS):
                row_index = index // columns
                col_index = index % columns
                button = tk.Button(
                    chars_frame,
                    text=character,
                    width=2,
                    font=("Arial", 8),
                    command=lambda current_char=character: insert_char(current_char),
                )
                button.grid(row=row_index, column=col_index, padx=1, pady=1)

        chars_frame.bind("<Configure>", relayout_chars)

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
            parent_frame,
            lambda: get_active_dicts()[0] if get_mode_type() == "eng_to_fan" else get_active_dicts()[1],
            get_mode_type,
            height=1,
            wrap=tk.WORD,
            font=("Arial", 11),
        )
        in_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        attach_clipboard_support(in_box)

        button_label = "Synonym Translate" if use_synonyms else "Translate"
        button_color = "#FF9800" if use_synonyms else "#4CAF50"

        tk.Button(
            parent_frame,
            text=button_label,
            command=trans,
            bg=button_color,
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)

        out_label = tk.Label(parent_frame, text="Output (Dwarf):", font=("Arial", 10, "bold"))
        out_label.pack(anchor="w", padx=15)

        out_box = scrolledtext.ScrolledText(
            parent_frame,
            height=1,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="#f4f4f4",
        )
        out_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        attach_clipboard_support(out_box)

    build_dictionary_tab(dictionary_frame)
    add_write_me_button(dictionary_frame)

    build_translation_tab(trans_frame, use_synonyms=False)
    build_translation_tab(synonym_frame, use_synonyms=True)
    add_write_me_button(trans_frame)
    add_write_me_button(synonym_frame)

    # ==================== RHYMING DICTIONARY INTERFACE ====================
    def build_rhyme_tab(parent_frame):
        """Build the Rhyming Dictionary tab's UI and logic inside
        `parent_frame`: a language picker, a "letters must match" depth
        control, a word input field, and two side-by-side output boxes
        (fantasy rhymes on the left, their English translations on the
        right)."""
        rhyme_lang_var = tk.StringVar(parent_frame, "Dwarf")
        rhyme_languages = list(LANGUAGE_FILES.keys())

        tk.Label(
            parent_frame,
            text="Rhyming Dictionary",
            font=("Arial", 12, "bold"),
        ).pack(pady=15)

        top_frame = tk.Frame(parent_frame)
        top_frame.pack(padx=15, pady=5)

        tk.Label(top_frame, text="Language:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 2))
        rhyme_lang_menu = tk.OptionMenu(top_frame, rhyme_lang_var, *rhyme_languages)
        rhyme_lang_menu.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(top_frame, text="Letters that must rhyme:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 2), pady=(19, 0))
        rhyme_letters_scale = tk.Scale(top_frame, from_=1, to=8, orient=tk.HORIZONTAL, length=140)
        rhyme_letters_scale.set(3)
        rhyme_letters_scale.pack(side=tk.LEFT)

        # Diacritic-sensitivity toggle: unpressed (default) treats accented
        # and unaccented letters as the same for rhyme matching (e.g. "Kás"
        # rhymes with "Kas"); pressed requires an exact diacritic match
        # (e.g. "Kás" only rhymes with "Kás").
        rhyme_diacritic_var = tk.BooleanVar(parent_frame, False)
        rhyme_diacritic_btn = tk.Checkbutton(
            top_frame,
            text="Diacritic match",
            variable=rhyme_diacritic_var,
            indicatoron=False,
            font=("Arial", 9),
            relief=tk.RAISED,
            command=lambda: generate_and_display_rhymes(),
        )
        rhyme_diacritic_btn.pack(side=tk.LEFT, padx=(15, 0))

        tk.Label(parent_frame, text="Word or Rime:", font=("Arial", 10, "bold")).pack(anchor="w", padx=15)

        # --- Special Character Buttons Frame for Rhymes ---
        rhyme_chars_frame = tk.Frame(parent_frame)
        rhyme_chars_frame.pack(fill=tk.X, padx=15, pady=2)

        def insert_rhyme_char(char):
            """Insert special character at cursor in the rhyme input field."""
            rhyme_word_entry.insert(tk.INSERT, char)
            rhyme_word_entry.focus_set()
            # Same fix as insert_char: the button click closes the
            # autocomplete popup via the app-wide handler before this runs,
            # so force a refresh against the newly-inserted character.
            rhyme_word_entry.event_generate("<KeyRelease>")

        def relayout_rhyme_chars(event=None):
            """Auto-wrap special character buttons based on frame width."""
            for widget in rhyme_chars_frame.winfo_children():
                widget.destroy()

            frame_width = rhyme_chars_frame.winfo_width()
            if frame_width < 10:
                frame_width = 450

            btn_width_px = 24
            columns = max(1, frame_width // btn_width_px)

            for index, character in enumerate(SPECIAL_CHARACTERS):
                row_index = index // columns
                col_index = index % columns
                button = tk.Button(
                    rhyme_chars_frame,
                    text=character,
                    width=2,
                    font=("Arial", 8),
                    command=lambda current_char=character: insert_rhyme_char(current_char),
                )
                button.grid(row=row_index, column=col_index, padx=1, pady=1)

        rhyme_chars_frame.bind("<Configure>", relayout_rhyme_chars)

        for index, character in enumerate(SPECIAL_CHARACTERS):
            row_index = index // 19
            col_index = index % 19
            button = tk.Button(
                rhyme_chars_frame,
                text=character,
                width=2,
                font=("Arial", 8),
                command=lambda current_char=character: insert_rhyme_char(current_char),
            )
            button.grid(row=row_index, column=col_index, padx=1, pady=1)

        word_frame = tk.Frame(parent_frame)
        word_frame.pack(padx=15, pady=(2, 5), fill=tk.X)

        rhyme_word_entry = AutoEntry(
            word_frame,
            get_d=lambda: rev_dicts_all.get(rhyme_lang_var.get(), {}),
            get_mode_type=lambda: "fan_to_eng",
            font=("Arial", 11)
        )
        rhyme_word_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        attach_clipboard_support(rhyme_word_entry)

        def generate_and_display_rhymes(*_args):
            """Look up every word in the selected fantasy language that
            rhymes (shares the selected number of trailing letters) with
            the word typed in the entry field, and display the matches on
            the left with their English translations lined up on the
            right."""
            word = rhyme_word_entry.get()
            language = rhyme_lang_var.get()
            letter_count = int(rhyme_letters_scale.get())
            diacritic_sensitive = rhyme_diacritic_var.get()
            reverse_dictionary_all = rev_dicts_all.get(language, {})

            rhyme_out_box.delete("1.0", tk.END)
            rhyme_trans_box.delete("1.0", tk.END)

            if not word.strip():
                return

            matches = find_rhyming_words(word, letter_count, reverse_dictionary_all, diacritic_sensitive)

            if not matches:
                rhyme_out_box.insert(tk.END, "(No rhymes found)")
                return

            rhyme_lines = []
            translation_lines = []
            for match in matches:
                translations = reverse_dictionary_all.get(match, [])
                translation_lines.append(", ".join(translations) if translations else "-")
                rhyme_lines.append(match)

            rhyme_out_box.insert(tk.END, "\n".join(rhyme_lines))
            rhyme_trans_box.insert(tk.END, "\n".join(translation_lines))

        def clear_rhyme_output():
            """Clear the word entry field and both rhyme output boxes."""
            rhyme_word_entry.delete(0, tk.END)
            rhyme_out_box.delete("1.0", tk.END)
            rhyme_trans_box.delete("1.0", tk.END)

        rhyme_word_entry.bind("<Return>", generate_and_display_rhymes)
        rhyme_lang_var.trace_add("write", lambda *_args: generate_and_display_rhymes())

        buttons_frame = tk.Frame(parent_frame)
        buttons_frame.pack(pady=5)

        tk.Button(
            buttons_frame,
            text="Find Rhymes",
            command=generate_and_display_rhymes,
            bg="#009688",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons_frame,
            text="Clear",
            command=clear_rhyme_output,
            font=("Arial", 9),
        ).pack(side=tk.LEFT, padx=5)

        output_frame = tk.Frame(parent_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))

        left_frame = tk.Frame(output_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_frame = tk.Frame(output_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(left_frame, text="Rhyming words:", font=("Arial", 10, "bold")).pack(anchor="w")
        rhyme_out_box = scrolledtext.ScrolledText(
            left_frame,
            height=10,
            width=10,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="#f4f4f4",
        )
        rhyme_out_box.pack(fill=tk.BOTH, expand=True)
        attach_clipboard_support(rhyme_out_box)

        tk.Label(right_frame, text="Translation (English):", font=("Arial", 10, "bold")).pack(anchor="w")
        rhyme_trans_box = scrolledtext.ScrolledText(
            right_frame,
            height=10,
            width=10,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="#f4f4f4",
        )
        rhyme_trans_box.pack(fill=tk.BOTH, expand=True)
        attach_clipboard_support(rhyme_trans_box)

    build_rhyme_tab(rhyme_frame)
    add_write_me_button(rhyme_frame)

    # ==================== KOBOL (KOBOLD) INTERFACE ====================
    tk.Label(
        kobold_frame,
        text="Kobold Gibberish Generator",
        font=("Arial", 12, "bold"),
    ).pack(pady=15)

    options_frame = tk.Frame(kobold_frame)
    options_frame.pack(pady=5)

    tk.Label(options_frame, text="Words in sentence:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5, pady=(19, 0))
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
    attach_clipboard_support(kobold_output_box)

    def generate_and_display_kobold():
        """Generate one Kobold gibberish sentence at the selected word count
        and append it to the Kobold output box."""
        count = word_count_scale.get()
        sentence = generate_kobold_sentence(count)
        kobold_output_box.insert(tk.END, sentence + "\n")
        kobold_output_box.see(tk.END)

    def clear_kobold_output():
        """Clear all text from the Kobold output box."""
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

    add_write_me_button(kobold_frame)

    # ==================== DIVINE LANGUAGE INTERFACE ====================
    tk.Label(
        divine_frame,
        text="Divine Language Generator",
        font=("Arial", 12, "bold"),
    ).pack(pady=15)

    divine_options_frame = tk.Frame(divine_frame)
    divine_options_frame.pack(pady=5)

    tk.Label(divine_options_frame, text="Words in sentence:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5, pady=(19, 0))
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
    attach_clipboard_support(divine_output_box)

    def generate_and_display_divine():
        """Generate one Divine-language gibberish sentence at the selected
        word count and append it to the Divine output box."""
        count = divine_word_count_scale.get()
        sentence = generate_divine_sentence(count)
        divine_output_box.insert(tk.END, sentence + "\n")
        divine_output_box.see(tk.END)

    def clear_divine_output():
        """Clear all text from the Divine output box."""
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

    add_write_me_button(divine_frame)

    # Set initial active view to Dictionary
    switch_to(dictionary_frame, btn_dictionary)

    root.mainloop()


if __name__ == "__main__":
    main()

# COMPILE WINDOWS .EXE
# pyinstaller --onefile --noconsole --icon=df_codexlogo.ico --add-data "df_codexlogo.ico;." --add-data "language_*.txt;." --add- data "synonyms.txt.gz;." df_codex.py


#DELETE SINGLE LETTER WORDS FROM THE SYNONYM DICTIONARY
#input_file = "synonyms.txt"
#output_file = "synonyms_cleaned.txt"
#
#with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
#    for line in infile:
#        parts = line.split("\t")
#
#        # Skip the line if the main word (first column) is a single character
#        if not parts or len(parts[0].strip()) <= 1:
#            continue
#
#        if len(parts) > 1:
#            word = parts[0]
#            # Split the synonyms by comma, filter out any single-character synonyms
#            synonyms = [s.strip() for s in parts[1].split(",")]
#            valid_synonyms = [s for s in synonyms if len(s) > 1]
#
#            # Rebuild the line with only valid synonyms
#            outfile.write(f"{word}\t{','.join(valid_synonyms)}\n")
#        else:
#            outfile.write(line)
#
#print(f"Cleaning complete. Saved to {output_file}")
#
# MAKE GZIP
#python -c "import gzip, shutil; shutil.copyfileobj(open('synonyms.txt', 'rb'), gzip.open('synonyms.txt.gz', 'wb'))"