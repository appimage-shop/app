import json
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class AppManager:
    def __init__(self):
        self.apps = []
        self.current_file = "app.json"
        self.load_json()

        # Janela principal
        self.window = Gtk.Window(title="Editor de Aplicativos")
        self.window.set_default_size(900, 650)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)

        # Estilo CSS adaptável ao tema do sistema
        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_data(b"""
            window {
                background-color: @theme_bg_color;
                font-family: 'Sans', sans-serif;
                color: @theme_fg_color;
            }
            button {
                padding: 8px 16px;
                margin: 4px;
                background-color: @theme_selected_bg_color;
                color: @theme_selected_fg_color;
                border: none;
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            button:hover {
                background-color: shade(@theme_selected_bg_color, 0.9);
            }
            button:active {
                background-color: shade(@theme_selected_bg_color, 0.8);
            }
            label {
                color: @theme_fg_color;
                font-size: 12px;
                font-weight: bold;
            }
            entry {
                padding: 6px;
                border: 1px solid @theme_base_color;
                border-radius: 4px;
                background-color: @theme_base_color;
                color: @theme_text_color;
            }
            frame {
                border: 1px solid @theme_base_color;
                border-radius: 4px;
                padding: 12px;
                background-color: @theme_base_color;
            }
            frame > label {
                color: @theme_selected_bg_color;
                font-weight: bold;
                margin-bottom: 8px;
            }
            notebook tab {
                padding: 8px 16px;
                background-color: @theme_bg_color;
                border-bottom: 2px solid @theme_base_color;
                color: @theme_fg_color;
            }
            notebook tab:checked {
                background-color: @theme_base_color;
                border-bottom: 2px solid @theme_selected_bg_color;
                color: @theme_selected_fg_color;
            }
            treeview {
                background-color: @theme_base_color;
                border: 1px solid @theme_base_color;
                color: @theme_text_color;
            }
            treeview:selected {
                background-color: @theme_selected_bg_color;
                color: @theme_selected_fg_color;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Contêiner principal
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.box.set_margin_top(12)
        self.box.set_margin_bottom(12)
        self.box.set_margin_start(12)
        self.box.set_margin_end(12)
        self.window.add(self.box)

        # Barra de menu
        self.create_menu_bar()

        # Notebook para abas
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.box.pack_start(self.notebook, True, True, 0)

        # Criação das visões
        self.create_list_view()
        self.create_edit_view()
        self.create_about_view()

        self.window.show_all()

    def load_json(self):
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
        except Exception as e:
            self.show_message("Erro", f"Não foi possível carregar {self.current_file}: {str(e)}", Gtk.MessageType.ERROR)

    def save_json(self):
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(self.apps, f, indent=4, ensure_ascii=False)
            self.show_message("Sucesso", "Alterações salvas com sucesso!", Gtk.MessageType.INFO)
        except Exception as e:
            self.show_message("Erro", f"Não foi possível salvar {self.current_file}: {str(e)}", Gtk.MessageType.ERROR)

    def show_message(self, title, message, message_type):
        dialog = Gtk.MessageDialog(
            parent=self.window, flags=0, message_type=message_type,
            buttons=Gtk.ButtonsType.OK, text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def open_file(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Abrir Arquivo JSON", parent=self.window, action=Gtk.FileChooserAction.OPEN,
            buttons=("Cancelar", Gtk.ResponseType.CANCEL, "Abrir", Gtk.ResponseType.OK)
        )
        filter_json = Gtk.FileFilter()
        filter_json.set_name("Arquivos JSON")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_file = dialog.get_filename()
            self.load_json()
            self.update_treeview()
            self.window.set_title(f"Editor de Aplicativos - {os.path.basename(self.current_file)}")
        dialog.destroy()

    def create_menu_bar(self):
        menu_box = Gtk.Box(spacing=8)
        accel_group = Gtk.AccelGroup()
        self.window.add_accel_group(accel_group)

        buttons = [
            ("list-add", "Novo", "Criar novo aplicativo", self.show_edit_view, None),
            ("document-open", "Abrir", "Abrir arquivo JSON (Ctrl+O)", self.open_file, (Gdk.KEY_o, Gdk.ModifierType.CONTROL_MASK)),
            ("document-save", "Salvar", "Salvar alterações (Ctrl+S)", self.save_json, (Gdk.KEY_s, Gdk.ModifierType.CONTROL_MASK)),
            ("help-about", "Sobre", "Sobre o aplicativo", lambda w: self.notebook.set_current_page(2), None)
        ]

        for icon, label, tooltip, callback, accel in buttons:
            button = Gtk.Button()
            button.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
            button.set_label(label)
            button.set_tooltip_text(tooltip)
            button.set_always_show_image(True)
            button.connect("clicked", callback)
            if accel:
                button.add_accelerator("clicked", accel_group, accel[0], accel[1], Gtk.AccelFlags.VISIBLE)
            menu_box.pack_start(button, False, False, 0)

        self.box.pack_start(menu_box, False, False, 0)

    def create_list_view(self):
        self.list_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # TreeView
        self.store = Gtk.ListStore(str, str, str)
        self.treeview = Gtk.TreeView(model=self.store)
        for i, title in enumerate(["Nome", "Versão", "Categoria"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_expand(True)
            column.set_sort_column_id(i)
            self.treeview.append_column(column)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        scrolled_window.add(self.treeview)
        self.list_view.pack_start(scrolled_window, True, True, 0)

        # Botões de ação
        button_box = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        edit_button = Gtk.Button(label="Editar")
        edit_button.set_image(Gtk.Image.new_from_icon_name("edit", Gtk.IconSize.BUTTON))
        edit_button.set_always_show_image(True)
        edit_button.connect("clicked", self.edit_selected)
        button_box.pack_start(edit_button, False, False, 0)

        delete_button = Gtk.Button(label="Excluir")
        delete_button.set_image(Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.BUTTON))
        delete_button.set_always_show_image(True)
        delete_button.connect("clicked", self.delete_selected)
        button_box.pack_start(delete_button, False, False, 0)

        self.list_view.pack_start(button_box, False, False, 0)
        self.notebook.append_page(self.list_view, Gtk.Label(label="Lista"))

    def create_edit_view(self):
        self.edit_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.entries = {}

        # Frame para formulário
        frame = Gtk.Frame(label="Informações do Aplicativo")
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(12)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)

        fields = [
            ("Nome", "name"),
            ("Descrição", "description"),
            ("Versão", "version"),
            ("Categoria", "category"),
            ("Categoria (Inglês)", "app"),
            ("URL do AppImage", "appimage_url"),
            ("URL do Ícone", "icon_url"),
            ("Nome do Ícone", "icon"),
            ("Detalhes", "details"),
            ("Capturas de Tela (separadas por vírgula)", "screenshots")
        ]

        for i, (label_text, field) in enumerate(fields):
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.END)
            grid.attach(label, 0, i, 1, 1)
            entry = Gtk.Entry()
            entry.set_width_chars(50)
            entry.set_placeholder_text(f"Digite {label_text.lower()}")
            grid.attach(entry, 1, i, 1, 1)
            self.entries[field] = entry

        scrolled_window.add(grid)
        frame.add(scrolled_window)
        self.edit_view.pack_start(frame, True, True, 0)

        # Botões
        button_box = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        save_button = Gtk.Button(label="Salvar")
        save_button.set_image(Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.BUTTON))
        save_button.set_always_show_image(True)
        save_button.connect("clicked", self.save_app)
        button_box.pack_start(save_button, False, False, 0)

        cancel_button = Gtk.Button(label="Cancelar")
        cancel_button.set_image(Gtk.Image.new_from_icon_name("process-stop", Gtk.IconSize.BUTTON))
        cancel_button.set_always_show_image(True)
        cancel_button.connect("clicked", lambda w: self.notebook.set_current_page(0))
        button_box.pack_start(cancel_button, False, False, 0)

        self.edit_view.pack_start(button_box, False, False, 0)
        self.notebook.append_page(self.edit_view, Gtk.Label(label="Editar"))

    def create_about_view(self):
        about_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        about_view.set_border_width(20)
        about_view.set_halign(Gtk.Align.CENTER)
        about_view.set_valign(Gtk.Align.CENTER)

        title_label = Gtk.Label(label="Editor de Aplicativos")
        title_label.set_markup("<span size='x-large' weight='bold'>Editor de Aplicativos</span>")
        about_view.pack_start(title_label, False, False, 0)

        info_label = Gtk.Label(label="Um editor simples para gerenciar arquivos JSON de aplicativos.\nDesenvolvido por Mateus Gonçalves.")
        info_label.set_justify(Gtk.Justification.CENTER)
        info_label.set_line_wrap(True)
        about_view.pack_start(info_label, False, False, 0)

        version_label = Gtk.Label(label="Versão 1.0")
        about_view.pack_start(version_label, False, False, 0)

        self.notebook.append_page(about_view, Gtk.Label(label="Sobre"))

    def validate_url(self, url):
        return url.startswith(("http://", "https://")) if url else True

    def update_treeview(self):
        self.store.clear()
        for app in self.apps:
            self.store.append([app.get("name", ""), app.get("version", ""), app.get("category", "")])

    def edit_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            index = model.get_path(treeiter).get_indices()[0]
            self.show_edit_view(index)
        else:
            self.show_message("Aviso", "Selecione um aplicativo para editar.", Gtk.MessageType.WARNING)

    def delete_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if not treeiter:
            self.show_message("Aviso", "Selecione um aplicativo para excluir.", Gtk.MessageType.WARNING)
            return

        dialog = Gtk.MessageDialog(
            parent=self.window, flags=0, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO, text="Confirmação",
            secondary_text="Deseja excluir este aplicativo permanentemente?"
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            index = model.get_path(treeiter).get_indices()[0]
            self.apps.pop(index)
            self.update_treeview()

    def show_edit_view(self, index):
        self.current_app_index = index
        for entry in self.entries.values():
            entry.set_text("")

        if index is not None and 0 <= index < len(self.apps):
            app = self.apps[index]
            for field, entry in self.entries.items():
                if field == " inhibitions":
                    entry.set_text(", ".join(app.get(field, [])))
                else:
                    entry.set_text(app.get(field, ""))

        self.notebook.set_current_page(1)

    def save_app(self, widget):
        app_data = {}
        for field, entry in self.entries.items():
            value = entry.get_text().strip()
            if field == "screenshots":
                app_data[field] = [url.strip() for url in value.split(",") if url.strip()]
            else:
                app_data[field] = value

        if not app_data["name"]:
            self.show_message("Aviso", "O campo 'Nome' é obrigatório.", Gtk.MessageType.WARNING)
            return

        for field in ["appimage_url", "icon_url"]:
            if app_data[field] and not self.validate_url(app_data[field]):
                self.show_message("Aviso", f"O campo '{field}' deve ser uma URL válida (http:// ou https://).", Gtk.MessageType.WARNING)
                return

        if self.current_app_index is not None and 0 <= self.current_app_index < len(self.apps):
            self.apps[self.current_app_index] = app_data
        else:
            self.apps.append(app_data)

        self.notebook.set_current_page(0)
        self.update_treeview()

if __name__ == "__main__":
    AppManager()
    Gtk.main()