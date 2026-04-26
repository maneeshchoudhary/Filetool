"""
File Tool — Kivy Android App
Tabs: Converter | Combiner | PDF Merger | Compressor
"""

import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

# ── Colors ─────────────────────────────────────────────────
BG      = get_color_from_hex('#F0F4F8')
ACCENT  = get_color_from_hex('#1A56DB')
ACCENT2 = get_color_from_hex('#1342A8')
SUCCESS = get_color_from_hex('#057A55')
DANGER  = get_color_from_hex('#C81E1E')
PURPLE  = get_color_from_hex('#7E3AF2')
WHITE   = get_color_from_hex('#FFFFFF')
SUBTEXT = get_color_from_hex('#6B7280')
TEXT    = get_color_from_hex('#111928')
ROW1    = get_color_from_hex('#EEF4FF')
ROW2    = get_color_from_hex('#FFFFFF')

Window.clearcolor = BG

IMAGE_EXTS = ('.jpg', '.jpeg', '.png')


# ══════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════

def get_downloads_path():
    """Return Downloads folder path on Android and PC."""
    try:
        from android.storage import primary_external_storage_path
        return os.path.join(primary_external_storage_path(), 'Download', 'FileTool')
    except ImportError:
        path = os.path.join(os.path.expanduser('~'), 'Downloads', 'FileTool')
    os.makedirs(path, exist_ok=True)
    return path


def unique_path(folder, filename):
    base, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    c = 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{base}_{c}{ext}")
        c += 1
    return path


def file_icon(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in ('.xlsx', '.xls', '.xlsm'): return '📗'
    if ext == '.pdf':   return '📕'
    if ext == '.docx':  return '📝'
    if ext == '.csv':   return '📄'
    if ext in IMAGE_EXTS: return '🖼'
    return '📄'


def make_btn(text, color, callback, height=dp(48)):
    btn = Button(
        text=text,
        background_color=color,
        background_normal='',
        color=WHITE,
        font_size=dp(14),
        bold=True,
        size_hint_y=None,
        height=height,
    )
    btn.bind(on_press=callback)
    return btn


def make_label(text, size=dp(12), color=None, bold=False, height=dp(24)):
    lbl = Label(
        text=text,
        font_size=size,
        color=color or SUBTEXT,
        bold=bold,
        size_hint_y=None,
        height=height,
        halign='left',
        valign='middle',
    )
    lbl.bind(size=lbl.setter('text_size'))
    return lbl


def show_file_picker(title, filters, on_select, multi=True):
    """Show a file chooser popup."""
    content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))

    fc = FileChooserListView(
        path=os.path.expanduser('~'),
        filters=filters,
        multiselect=multi,
        size_hint_y=1,
    )
    content.add_widget(fc)

    btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))

    popup = Popup(title=title, content=content,
                  size_hint=(.95, .85))

    def on_cancel(_):
        popup.dismiss()

    def on_ok(_):
        if fc.selection:
            on_select(fc.selection)
        popup.dismiss()

    btn_row.add_widget(make_btn('Cancel', DANGER, on_cancel, dp(44)))
    btn_row.add_widget(make_btn('Select', SUCCESS, on_ok, dp(44)))
    content.add_widget(btn_row)
    popup.open()


def show_message(title, message, color=SUCCESS):
    content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
    lbl = Label(text=message, font_size=dp(13), color=TEXT,
                halign='left', valign='top')
    lbl.bind(size=lbl.setter('text_size'))
    content.add_widget(lbl)
    btn = make_btn('OK', color, lambda _: popup.dismiss(), dp(44))
    content.add_widget(btn)
    popup = Popup(title=title, content=content,
                  size_hint=(.85, None), height=dp(220))
    popup.open()


# ══════════════════════════════════════════════════════════
#  FILE LIST WIDGET
# ══════════════════════════════════════════════════════════

class FileListWidget(BoxLayout):
    """Scrollable list of files with remove buttons."""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(2),
                         size_hint_y=None, **kwargs)
        self.files = []
        self.bind(minimum_height=self.setter('height'))

    def add_files(self, paths):
        existing = {f for f in self.files}
        for p in paths:
            if p not in existing:
                self.files.append(p)
        self._refresh()

    def remove_file(self, path):
        if path in self.files:
            self.files.remove(path)
        self._refresh()

    def clear(self):
        self.files.clear()
        self._refresh()

    def _refresh(self):
        self.clear_widgets()
        for i, fp in enumerate(self.files):
            row_bg = ROW1 if i % 2 == 0 else ROW2
            row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))

            icon_lbl = make_label(
                file_icon(fp) + ' ' + os.path.basename(fp),
                size=dp(11), color=TEXT, height=dp(38)
            )
            row.add_widget(icon_lbl)

            size_str = ''
            try:
                sz = os.path.getsize(fp)
                size_str = f'{sz/1024:.0f}KB' if sz < 1024**2 else f'{sz/1024/1024:.1f}MB'
            except Exception:
                pass
            row.add_widget(make_label(size_str, size=dp(10),
                                      color=SUBTEXT, height=dp(38)))

            del_btn = Button(
                text='✕', font_size=dp(13),
                size_hint=(None, None), size=(dp(32), dp(32)),
                background_color=DANGER, background_normal='',
                color=WHITE,
            )
            del_btn.bind(on_press=lambda _, p=fp: self.remove_file(p))
            row.add_widget(del_btn)
            self.add_widget(row)


# ══════════════════════════════════════════════════════════
#  STATUS BAR
# ══════════════════════════════════════════════════════════

class StatusBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical',
                         size_hint_y=None, height=dp(60),
                         spacing=dp(4), **kwargs)
        self.pb = ProgressBar(max=100, value=0,
                              size_hint_y=None, height=dp(6))
        self.lbl = make_label('Ready', size=dp(11),
                              color=SUBTEXT, height=dp(20))
        self.pb.opacity = 0
        self.add_widget(self.pb)
        self.add_widget(self.lbl)

    def set(self, text, color=None, loading=False):
        Clock.schedule_once(lambda dt: self._set(text, color, loading))

    def _set(self, text, color, loading):
        self.lbl.text  = text
        self.lbl.color = color or SUBTEXT
        self.pb.opacity = 1 if loading else 0
        if loading:
            self._animate()

    def _animate(self):
        if self.pb.opacity:
            self.pb.value = (self.pb.value + 5) % 100
            Clock.schedule_once(lambda dt: self._animate(), .05)


# ══════════════════════════════════════════════════════════
#  TAB 1 — CONVERTER
# ══════════════════════════════════════════════════════════

CONV_MODES = {
    '📄 CSV  →  📗 Excel':   'csv2xlsx',
    '📗 Excel  →  📄 CSV':   'xlsx2csv',
    '📕 PDF  →  📗 Excel':   'pdf2xlsx',
    '📗 Excel  →  📕 PDF':   'xlsx2pdf',
    '🖼 JPG/PNG  →  📕 PDF': 'img2pdf',
    '📕 PDF  →  🖼 JPG':     'pdf2jpg',
}

CONV_FILTERS = {
    'csv2xlsx': ['*.csv'],
    'xlsx2csv': ['*.xlsx','*.xls','*.xlsm'],
    'pdf2xlsx': ['*.pdf'],
    'xlsx2pdf': ['*.xlsx','*.xls','*.xlsm'],
    'img2pdf':  ['*.jpg','*.jpeg','*.png'],
    'pdf2jpg':  ['*.pdf'],
}


class ConverterTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10),
                         padding=dp(12), **kwargs)
        self._files = []
        self._build()

    def _build(self):
        # Mode spinner
        self.add_widget(make_label('Conversion Type', bold=True,
                                   color=TEXT, height=dp(20)))
        self.spinner = Spinner(
            text=list(CONV_MODES.keys())[0],
            values=list(CONV_MODES.keys()),
            size_hint_y=None, height=dp(44),
            background_color=ACCENT, background_normal='',
            color=WHITE, font_size=dp(13),
        )
        self.spinner.bind(text=lambda _, t: self._on_mode())
        self.add_widget(self.spinner)

        # File list
        self.add_widget(make_label('Files', bold=True,
                                   color=TEXT, height=dp(20)))
        sv = ScrollView(size_hint=(1, 1))
        self.file_list = FileListWidget()
        sv.add_widget(self.file_list)
        self.add_widget(sv)

        # Buttons
        self.add_widget(make_btn('➕  Add Files', ACCENT, self._add_files))
        self.add_widget(make_btn('✖  Clear All', DANGER, lambda _: self._clear()))
        self.add_widget(make_btn('🔄  CONVERT', SUCCESS, self._convert))

        # Status
        self.status = StatusBar()
        self.add_widget(self.status)

    def _on_mode(self):
        self.file_list.clear()
        self.status.set('Mode changed — add files.')

    def _add_files(self, _):
        mode    = CONV_MODES[self.spinner.text]
        filters = CONV_FILTERS.get(mode, ['*.*'])

        def on_select(paths):
            self.file_list.add_files(paths)
            self.status.set(f'✔ {len(self.file_list.files)} file(s) added.')

        show_file_picker('Select Files', filters, on_select)

    def _clear(self):
        self.file_list.clear()
        self.status.set('Cleared.')

    def _convert(self, _):
        files = self.file_list.files
        if not files:
            self.status.set('⚠ Add files first!', color=DANGER)
            return
        mode = CONV_MODES[self.spinner.text]
        self.status.set('⏳ Converting…', loading=True)
        threading.Thread(target=self._run_convert,
                         args=(files, mode), daemon=True).start()

    def _run_convert(self, files, mode):
        out_dir = get_downloads_path()
        done = 0; errors = []

        try:
            import pandas as pd

            for fp in files:
                try:
                    base = os.path.splitext(os.path.basename(fp))[0]

                    if mode == 'csv2xlsx':
                        out = unique_path(out_dir, base + '.xlsx')
                        pd.read_csv(fp).to_excel(out, index=False)

                    elif mode == 'xlsx2csv':
                        out = unique_path(out_dir, base + '.csv')
                        pd.read_excel(fp).to_csv(out, index=False)

                    elif mode == 'pdf2xlsx':
                        from pypdf import PdfReader
                        out = unique_path(out_dir, base + '.xlsx')
                        rows = []
                        reader = PdfReader(fp)
                        for page in reader.pages:
                            text = page.extract_text() or ''
                            for line in text.splitlines():
                                if line.strip():
                                    rows.append([line.strip()])
                        pd.DataFrame(rows).to_excel(out, index=False, header=False)

                    elif mode == 'xlsx2pdf':
                        # Save as CSV (reportlab not available on Android)
                        out = unique_path(out_dir, base + '.csv')
                        df = pd.read_excel(fp, dtype=str).fillna('')
                        df.to_csv(out, index=False)

                    elif mode == 'img2pdf':
                        from PIL import Image as PILImage
                        out = unique_path(out_dir, base + '.pdf')
                        img = PILImage.open(fp).convert('RGB')
                        img.save(out, 'PDF', resolution=150)

                    elif mode == 'pdf2jpg':
                        raise Exception('PDF to JPG is not supported on Android. Use a PC for this conversion.')

                    done += 1
                except Exception as e:
                    errors.append(f'{os.path.basename(fp)}: {e}')

        except ImportError as e:
            Clock.schedule_once(lambda dt: show_message(
                'Missing Library', str(e), DANGER))
            self.status.set(f'❌ {e}', color=DANGER)
            return

        if errors:
            msg = f'✔ {done} ok, ❌ {len(errors)} failed\n\n' + '\n'.join(errors[:3])
            Clock.schedule_once(lambda dt: show_message('Partial Done', msg, DANGER))
            self.status.set(f'⚠ {done} ok, {len(errors)} failed', color=DANGER)
        else:
            msg = f'✅ {done} file(s) converted!\nSaved to:\n{out_dir}'
            Clock.schedule_once(lambda dt: show_message('Done!', msg, SUCCESS))
            self.status.set(f'✅ {done} converted! → {out_dir}', color=SUCCESS)


# ══════════════════════════════════════════════════════════
#  TAB 2 — COMBINER
# ══════════════════════════════════════════════════════════

class CombinerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10),
                         padding=dp(12), **kwargs)
        self._build()

    def _build(self):
        # Output type
        self.add_widget(make_label('Output Type', bold=True,
                                   color=TEXT, height=dp(20)))
        type_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.xlsx_btn = ToggleButton(
            text='📗 Excel', group='comb_type', state='down',
            background_color=ACCENT, background_normal='',
            background_down='', color=WHITE, font_size=dp(13),
        )
        self.csv_btn = ToggleButton(
            text='📄 CSV', group='comb_type',
            background_color=SUBTEXT, background_normal='',
            background_down='', color=WHITE, font_size=dp(13),
        )
        type_row.add_widget(self.xlsx_btn)
        type_row.add_widget(self.csv_btn)
        self.add_widget(type_row)

        # Options
        self.add_widget(make_label('Options', bold=True,
                                   color=TEXT, height=dp(20)))
        opts = BoxLayout(orientation='vertical', size_hint_y=None,
                         height=dp(110), spacing=dp(6))

        def opt_row(text):
            row = BoxLayout(size_hint_y=None, height=dp(32))
            sw  = Switch(active=True, size_hint=(None, None),
                         size=(dp(60), dp(32)))
            row.add_widget(make_label(text, color=TEXT, height=dp(32)))
            row.add_widget(sw)
            return row, sw

        r1, self.skip_sw  = opt_row('Skip empty rows')
        r2, self.src_sw   = opt_row('Add source filename')
        r3, self.sheet_sw = opt_row('Sheet per file (Excel)')
        opts.add_widget(r1); opts.add_widget(r2); opts.add_widget(r3)
        self.add_widget(opts)

        # File list
        self.add_widget(make_label('CSV / Excel Files', bold=True,
                                   color=TEXT, height=dp(20)))
        sv = ScrollView(size_hint=(1, 1))
        self.file_list = FileListWidget()
        sv.add_widget(self.file_list)
        self.add_widget(sv)

        self.add_widget(make_btn('➕  Add Files', ACCENT, self._add_files))
        self.add_widget(make_btn('✖  Clear All', DANGER,
                                  lambda _: self.file_list.clear()))
        self.add_widget(make_btn('🔀  COMBINE', ACCENT2, self._combine))

        self.status = StatusBar()
        self.add_widget(self.status)

    def _add_files(self, _):
        show_file_picker(
            'Select CSV / Excel Files',
            ['*.csv','*.xlsx','*.xls','*.xlsm'],
            lambda paths: (self.file_list.add_files(paths),
                           self.status.set(f'✔ {len(self.file_list.files)} file(s) added.'))
        )

    def _combine(self, _):
        files = self.file_list.files
        if not files:
            self.status.set('⚠ Add files first!', color=DANGER); return
        self.status.set('⏳ Combining…', loading=True)
        is_xlsx   = self.xlsx_btn.state == 'down'
        skip_empty = self.skip_sw.active
        add_source = self.src_sw.active
        sheet_per  = self.sheet_sw.active and is_xlsx
        threading.Thread(
            target=self._run,
            args=(files, is_xlsx, skip_empty, add_source, sheet_per),
            daemon=True
        ).start()

    def _run(self, files, is_xlsx, skip_empty, add_source, sheet_per):
        try:
            import pandas as pd
            out_dir = get_downloads_path()
            dfs = {}; combined = []

            for fp in files:
                ext = os.path.splitext(fp)[1].lower()
                df  = pd.read_csv(fp, dtype=str) if ext == '.csv' \
                      else pd.read_excel(fp, dtype=str)
                if skip_empty: df.dropna(how='all', inplace=True)
                name = os.path.basename(fp)
                if add_source: df.insert(0, 'Source File', name)
                if sheet_per:
                    sn = os.path.splitext(name)[0][:31]
                    orig, c = sn, 1
                    while sn in dfs: sn = f'{orig[:28]}_{c}'; c += 1
                    dfs[sn] = df
                else:
                    combined.append(df)

            ext = '.xlsx' if is_xlsx else '.csv'
            out = unique_path(out_dir, 'combined' + ext)

            if sheet_per:
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    for sn, df in dfs.items():
                        df.to_excel(writer, sheet_name=sn, index=False)
            else:
                result = pd.concat(combined, ignore_index=True)
                if is_xlsx: result.to_excel(out, index=False)
                else:        result.to_csv(out, index=False)

            msg = f'✅ {len(files)} files combined!\nSaved:\n{out}'
            Clock.schedule_once(lambda dt: show_message('Done!', msg, SUCCESS))
            self.status.set(f'✅ Saved → {out}', color=SUCCESS)

        except Exception as e:
            Clock.schedule_once(lambda dt: show_message('Error', str(e), DANGER))
            self.status.set(f'❌ {e}', color=DANGER)


# ══════════════════════════════════════════════════════════
#  TAB 3 — PDF MERGER
# ══════════════════════════════════════════════════════════

class PdfMergerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10),
                         padding=dp(12), **kwargs)
        self._pdf_files = []  # list of [path, page_spec]
        self._build()

    def _build(self):
        self.add_widget(make_label(
            'Add PDFs. Page range optional (e.g. 1-3,5)',
            size=dp(11), color=SUBTEXT, height=dp(20)
        ))

        sv = ScrollView(size_hint=(1, 1))
        self.list_layout = GridLayout(
            cols=1, spacing=dp(4),
            size_hint_y=None, padding=(0, dp(4))
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv.add_widget(self.list_layout)
        self.add_widget(sv)

        self.add_widget(make_btn('➕  Add PDF Files', DANGER, self._add_files))
        self.add_widget(make_btn('✖  Clear All', SUBTEXT,
                                  lambda _: self._clear()))
        self.add_widget(make_btn('📕  MERGE PDFs', DANGER, self._merge))

        self.status = StatusBar()
        self.add_widget(self.status)

    def _add_files(self, _):
        show_file_picker('Select PDF Files', ['*.pdf'],
                         self._on_select)

    def _on_select(self, paths):
        existing = [x[0] for x in self._pdf_files]
        for p in paths:
            if p not in existing:
                self._pdf_files.append([p, ''])
        self._refresh()
        self.status.set(f'✔ {len(self._pdf_files)} PDF(s) added.')

    def _clear(self):
        self._pdf_files.clear()
        self._refresh()

    def _refresh(self):
        self.list_layout.clear_widgets()
        for i, item in enumerate(self._pdf_files):
            fp, spec = item
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))

            num = make_label(f'{i+1:02d}', size=dp(12), color=WHITE,
                             height=dp(44))
            num.size_hint_x = None; num.width = dp(28)
            row.add_widget(num)

            row.add_widget(make_label(
                f'📕 {os.path.basename(fp)}',
                size=dp(11), color=TEXT, height=dp(44)
            ))

            page_inp = TextInput(
                text=spec, hint_text='Pages e.g. 1-3',
                multiline=False, font_size=dp(11),
                size_hint=(None, None), size=(dp(110), dp(36)),
            )
            idx = i

            def make_cb(index, inp):
                def cb(inst, val):
                    self._pdf_files[index][1] = val
                inp.bind(text=cb)

            make_cb(idx, page_inp)
            row.add_widget(page_inp)

            del_btn = Button(
                text='✕', font_size=dp(13),
                size_hint=(None, None), size=(dp(32), dp(36)),
                background_color=DANGER, background_normal='',
                color=WHITE,
            )
            del_btn.bind(on_press=lambda _, p=fp: self._remove(p))
            row.add_widget(del_btn)
            self.list_layout.add_widget(row)

    def _remove(self, path):
        self._pdf_files = [x for x in self._pdf_files if x[0] != path]
        self._refresh()

    def _merge(self, _):
        if not self._pdf_files:
            self.status.set('⚠ Add PDF files first!', color=DANGER); return
        self.status.set('⏳ Merging PDFs…', loading=True)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            try:
                from pypdf import PdfWriter, PdfReader
            except ImportError:
                from PyPDF2 import PdfWriter, PdfReader

            writer = PdfWriter()
            total  = 0
            for fp, spec in self._pdf_files:
                reader  = PdfReader(fp)
                n       = len(reader.pages)
                indices = self._parse_pages(spec, n)
                for idx in indices:
                    writer.add_page(reader.pages[idx])
                    total += 1

            out_dir = get_downloads_path()
            out     = unique_path(out_dir, 'merged.pdf')
            with open(out, 'wb') as fh:
                writer.write(fh)

            msg = (f'✅ Merge complete!\nFiles: {len(self._pdf_files)}\n'
                   f'Pages: {total}\nSaved:\n{out}')
            Clock.schedule_once(lambda dt: show_message('Done!', msg, SUCCESS))
            self.status.set(f'✅ {total} pages merged → {out}', color=SUCCESS)

        except Exception as e:
            Clock.schedule_once(lambda dt: show_message('Error', str(e), DANGER))
            self.status.set(f'❌ {e}', color=DANGER)

    @staticmethod
    def _parse_pages(page_str, max_pages):
        if not page_str.strip():
            return list(range(max_pages))
        pages = []
        for part in page_str.split(','):
            part = part.strip()
            if '-' in part:
                a, b = part.split('-', 1)
                try:
                    pages.extend(range(max(1, int(a)), min(int(b), max_pages) + 1))
                except ValueError: pass
            else:
                try: pages.append(int(part))
                except ValueError: pass
        seen = set(); result = []
        for p in pages:
            idx = p - 1
            if 0 <= idx < max_pages and idx not in seen:
                seen.add(idx); result.append(idx)
        return result


# ══════════════════════════════════════════════════════════
#  TAB 4 — COMPRESSOR
# ══════════════════════════════════════════════════════════

class CompressorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10),
                         padding=dp(12), **kwargs)
        self._build()

    def _build(self):
        # Settings
        self.add_widget(make_label('Target Size (KB)',
                                   bold=True, color=TEXT, height=dp(20)))
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.use_target = Switch(active=True, size_hint=(None, None),
                                  size=(dp(60), dp(40)))
        row.add_widget(self.use_target)
        self.target_inp = TextInput(
            text='500', hint_text='KB',
            multiline=False, font_size=dp(14),
            size_hint_y=None, height=dp(40),
        )
        row.add_widget(self.target_inp)
        self.add_widget(row)

        self.add_widget(make_label('Image Quality (1–95)',
                                   bold=True, color=TEXT, height=dp(20)))
        from kivy.uix.slider import Slider
        self.quality_slider = Slider(min=1, max=95, value=75,
                                      size_hint_y=None, height=dp(36))
        self.q_label = make_label('75', color=ACCENT, height=dp(20))
        self.quality_slider.bind(
            value=lambda _, v: setattr(self.q_label, 'text', str(int(v))))
        self.add_widget(self.quality_slider)
        self.add_widget(self.q_label)

        # File list
        self.add_widget(make_label('PDF / JPG / PNG Files',
                                   bold=True, color=TEXT, height=dp(20)))
        sv = ScrollView(size_hint=(1, 1))
        self.file_list = FileListWidget()
        sv.add_widget(self.file_list)
        self.add_widget(sv)

        self.add_widget(make_btn('➕  Add Files', PURPLE, self._add_files))
        self.add_widget(make_btn('✖  Clear All', DANGER,
                                  lambda _: self.file_list.clear()))
        self.add_widget(make_btn('🗜  COMPRESS', PURPLE, self._compress))

        self.status = StatusBar()
        self.add_widget(self.status)

    def _add_files(self, _):
        show_file_picker(
            'Select PDF / Image Files',
            ['*.pdf', '*.jpg', '*.jpeg', '*.png'],
            lambda paths: self.file_list.add_files(paths)
        )

    def _compress(self, _):
        files = self.file_list.files
        if not files:
            self.status.set('⚠ Add files first!', color=DANGER); return
        use_target = self.use_target.active
        try:
            target_kb = float(self.target_inp.text) if use_target else None
        except ValueError:
            target_kb = None
        quality = int(self.quality_slider.value)
        self.status.set('⏳ Compressing…', loading=True)
        threading.Thread(
            target=self._run,
            args=(files, target_kb, quality, use_target),
            daemon=True
        ).start()

    def _run(self, files, target_kb, quality, use_target):
        out_dir = get_downloads_path()
        done = 0; errors = []

        for fp in files:
            try:
                ext  = os.path.splitext(fp)[1].lower()
                base = os.path.splitext(os.path.basename(fp))[0]
                out  = unique_path(out_dir, base + '_compressed' + ext)

                if ext == '.pdf':
                    import pikepdf
                    with pikepdf.open(fp) as pdf:
                        pdf.save(out, compress_streams=True)
                elif ext in IMAGE_EXTS:
                    import io
                    from PIL import Image as PILImage
                    img = PILImage.open(fp)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    fmt = 'JPEG' if ext in ('.jpg','.jpeg') else 'PNG'
                    if use_target and target_kb:
                        lo, hi, best_q = 1, 95, quality
                        for _ in range(10):
                            mid = (lo + hi) // 2
                            buf = io.BytesIO()
                            img.save(buf, fmt, quality=mid, optimize=True)
                            if buf.tell() / 1024 <= target_kb:
                                best_q = mid; lo = mid + 1
                            else:
                                hi = mid - 1
                        img.save(out, fmt, quality=best_q, optimize=True)
                    else:
                        img.save(out, fmt, quality=quality, optimize=True)
                done += 1
            except Exception as e:
                errors.append(f'{os.path.basename(fp)}: {e}')

        if errors:
            msg = f'✔ {done} ok, ❌ {len(errors)} failed\n\n' + '\n'.join(errors[:3])
            Clock.schedule_once(lambda dt: show_message('Partial', msg, DANGER))
            self.status.set(f'⚠ {done} ok, {len(errors)} failed', color=DANGER)
        else:
            msg = f'✅ {done} file(s) compressed!\nSaved to:\n{out_dir}'
            Clock.schedule_once(lambda dt: show_message('Done!', msg, SUCCESS))
            self.status.set(f'✅ {done} compressed → {out_dir}', color=SUCCESS)


# ══════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════

class FileToolApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(
            size_hint_y=None, height=dp(52),
            padding=(dp(16), dp(8)),
            spacing=dp(10),
        )
        header.canvas.before.add(
            __import__('kivy.graphics', fromlist=['Color']).Color(
                *get_color_from_hex('#1A56DB'))
        )
        from kivy.graphics import Rectangle, Color
        with header.canvas.before:
            Color(*ACCENT)
            self._header_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda w, v: setattr(self._header_rect, 'pos', v),
                    size=lambda w, v: setattr(self._header_rect, 'size', v))

        title_lbl = Label(
            text='📊 File Tool',
            font_size=dp(18), bold=True,
            color=WHITE, halign='left',
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))
        sub_lbl = Label(
            text='Convert · Merge · Compress',
            font_size=dp(10), color=get_color_from_hex('#93C5FD'),
            halign='left',
        )
        sub_lbl.bind(size=sub_lbl.setter('text_size'))

        title_box = BoxLayout(orientation='vertical')
        title_box.add_widget(title_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)
        root.add_widget(header)

        # Tabs
        tp = TabbedPanel(do_default_tab=False)
        tp.tab_width = dp(90)

        tabs = [
            ('🔄 Convert', ConverterTab()),
            ('🔀 Combine', CombinerTab()),
            ('📕 PDF',     PdfMergerTab()),
            ('🗜 Compress',CompressorTab()),
        ]
        for title, widget in tabs:
            item = TabbedPanelItem(text=title, font_size=dp(12))
            scroll = ScrollView()
            scroll.add_widget(widget)
            item.add_widget(scroll)
            tp.add_widget(item)

        tp.default_tab = tp.tab_list[-1]  # select first
        root.add_widget(tp)
        return root


if __name__ == '__main__':
    FileToolApp().run()
