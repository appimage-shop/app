import json
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class AppManager:
    def __init__(self):
        self.apps = []
        self.current_file = "app.json"
        self.last_directory = os.path.expanduser("~")  # Diretório inicial
        self.load_json()

        # Janela principal
        self.window = Gtk.Window(title="Editor App.json")
        self.window.set_default_size(800, 600)
        self.window.connect("destroy", Gtk.main_quit)

        # Contêiner principal
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(self.box)

        # Barra de menu
        self.create_menu_bar()

        # Notebook para abas
        self.notebook = Gtk.Notebook()
        self.box.pack_start(self.notebook, True, True, 0)

        # Visão da lista
        self.create_list_view()

        # Visão de edição
        self.create_edit_view()

        # Mostrar visão da lista por padrão
        self.show_list_view()

        self.window.show_all()

    def load_json(self):
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
        except json.JSONDecodeError as e:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Erro ao carregar {self.current_file}: Formato JSON inválido ({str(e)})"
            )
            dialog.run()
            dialog.destroy()
        except Exception as e:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Falha ao carregar {self.current_file}: {str(e)}"
            )
            dialog.run()
            dialog.destroy()

    def save_json(self):
        try:
            if os.path.exists(self.current_file):
                dialog = Gtk.MessageDialog(
                    parent=self.window, flags=0, message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO, text="O arquivo já existe. Deseja sobrescrever?"
                )
                response = dialog.run()
                dialog.destroy()
                if response != Gtk.ResponseType.YES:
                    return

            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(self.apps, f, indent=4, ensure_ascii=False)
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK, text="Alterações salvas com sucesso!"
            )
            dialog.run()
            dialog.destroy()
        except Exception as e:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Falha ao salvar {self.current_file}: {str(e)}"
            )
            dialog.run()
            dialog.destroy()

    def open_file(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Abrir arquivo JSON", parent=self.window, action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_current_folder(self.last_directory)
        filter_json = Gtk.FileFilter()
        filter_json.set_name("Arquivos JSON")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_file = dialog.get_filename()
            self.last_directory = os.path.dirname(self.current_file)
            self.load_json()
            self.update_treeview()
            self.window.set_title(f"Editor App.json - {self.current_file}")

        dialog.destroy()

    def create_menu_bar(self):
        menubar = Gtk.MenuBar()

        # Menu Arquivo
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="Arquivo")
        file_item.set_submenu(file_menu)

        open_item = Gtk.MenuItem(label="Abrir")
        open_item.connect("activate", self.open_file)
        file_menu.append(open_item)

        save_item = Gtk.MenuItem(label="Salvar")
        save_item.connect("activate", lambda w: self.save_json())
        file_menu.append(save_item)

        exit_item = Gtk.MenuItem(label="Sair")
        exit_item.connect("activate", Gtk.main_quit)
        file_menu.append(exit_item)

        menubar.append(file_item)

        # Menu Aplicativos
        apps_menu = Gtk.Menu()
        apps_item = Gtk.MenuItem(label="Aplicativos")
        apps_item.set_submenu(apps_menu)

        list_item = Gtk.MenuItem(label="Listar")
        list_item.connect("activate", lambda w: self.show_list_view())
        apps_menu.append(list_item)

        add_item = Gtk.MenuItem(label="Adicionar")
        add_item.connect("activate", lambda w: self.show_edit_view(None))
        apps_menu.append(add_item)

        menubar.append(apps_item)

        # Menu Ajuda
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Ajuda")
        help_item.set_submenu(help_menu)

        about_item = Gtk.MenuItem(label="Sobre")
        about_item.connect("activate", self.show_about_dialog)
        help_menu.append(about_item)

        menubar.append(help_item)

        self.box.pack_start(menubar, False, False, 0)

    def show_about_dialog(self, widget):
        about_dialog = Gtk.Dialog(title="Sobre", parent=self.window, flags=0)
        about_dialog.set_default_size(300, 200)
        about_dialog.set_modal(True)

        content_area = about_dialog.get_content_area()

        title_label = Gtk.Label()
        title_label.set_markup("<b>Editor App.json</b>")
        content_area.pack_start(title_label, False, False, 10)

        dev_label = Gtk.Label(label="Desenvolvido por: Mateus Gonçalves")
        content_area.pack_start(dev_label, False, False, 0)

        license_label = Gtk.Label(label="Licença: GNU General Public License v3.0 (GPL-3.0)")
        content_area.pack_start(license_label, False, False, 0)

        desc_label = Gtk.Label(label="Um aplicativo para gerenciar arquivos JSON de aplicativos, permitindo adicionar, editar e excluir entradas.")
        desc_label.set_line_wrap(True)
        content_area.pack_start(desc_label, False, False, 0)

        about_dialog.show_all()
        about_dialog.run()
        about_dialog.destroy()

    def create_list_view(self):
        self.list_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # TreeView
        self.store = Gtk.ListStore(str, str, str, str, int)
        self.treeview = Gtk.TreeView(model=self.store)
        for i, column_title in enumerate(["Nome", "Versão", "Categoria", "Descrição", "Capturas"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.treeview)
        self.list_view.pack_start(scrolled_window, True, True, 0)

        # Botões
        button_box = Gtk.Box(spacing=6)
        edit_button = Gtk.Button(label="Editar Selecionado")
        edit_button.connect("clicked", self.edit_selected)
        button_box.pack_start(edit_button, False, False, 0)

        delete_button = Gtk.Button(label="Excluir Selecionado")
        delete_button.connect("clicked", self.delete_selected)
        button_box.pack_start(delete_button, False, False, 0)

        self.list_view.pack_start(button_box, False, False, 0)
        self.notebook.append_page(self.list_view, Gtk.Label(label="Lista de Aplicativos"))
        self.update_treeview()

    def create_edit_view(self):
        self.edit_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.entries = {}

        fields = [
            ("Nome", "name"),
            ("Descrição", "description"),
            ("URL do AppImage", "appimage_url"),
            ("URL do Ícone", "icon_url"),
            ("Nome do Ícone (Em minúsculo)", "icon"),
            ("Categoria", "category"),
            ("Categoria (Em Inglês)", "app"),
            ("Versão", "version"),
            ("Detalhes", "details")
        ]

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)

        for i, (label_text, field) in enumerate(fields):
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.END)
            grid.attach(label, 0, i, 1, 1)

            entry = Gtk.Entry()
            entry.set_width_chars(50)
            grid.attach(entry, 1, i, 1, 1)
            self.entries[field] = entry

        # Campo dinâmico para capturas de tela
        screenshots_label = Gtk.Label(label="Capturas de Tela")
        screenshots_label.set_halign(Gtk.Align.END)
        grid.attach(screenshots_label, 0, len(fields), 1, 1)

        self.screenshots_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.screenshots_list = Gtk.ListBox()
        self.screenshots_box.pack_start(self.screenshots_list, True, True, 0)

        add_screenshot_button = Gtk.Button(label="Adicionar URL")
        add_screenshot_button.connect("clicked", self.add_screenshot_entry)
        self.screenshots_box.pack_start(add_screenshot_button, False, False, 0)

        grid.attach(self.screenshots_box, 1, len(fields), 1, 1)

        self.edit_view.pack_start(grid, False, False, 0)

        button_box = Gtk.Box(spacing=6)
        save_button = Gtk.Button(label="Salvar Aplicativo")
        save_button.connect("clicked", self.save_app)
        button_box.pack_start(save_button, False, False, 0)

        cancel_button = Gtk.Button(label="Cancelar")
        cancel_value = lambda w: self.show_list_view()
        cancel_button.connect("clicked", cancel_value)
        button_box.pack_start(cancel_button, False, False, 0)

        self.edit_view.pack_start(button_box, False, False, 0)
        self.notebook.append_page(self.edit_view, Gtk.Label(label="Editar/Adicionar"))

    def add_screenshot_entry(self, widget, url=""):
        entry = Gtk.Entry()
        entry.set_text(url)
        remove_button = Gtk.Button(label="Remover")
        remove_button.connect("clicked", lambda w: self.screenshots_list.remove(entry.get_parent()))
        box = Gtk.Box()
        box.pack_start(entry, True, True, 0)
        box.pack_start(remove_button, False, False, 0)
        self.screenshots_list.add(box)
        box.show_all()

    def update_treeview(self):
        self.store.clear()
        for app in self.apps:
            screenshots_count = len(app.get("screenshots", []))
            self.store.append([app["name"], app["version"], app["category"], app.get("description", ""), screenshots_count])

    def show_list_view(self):
        self.notebook.set_current_page(0)
        self.update_treeview()

    def show_edit_view(self, index):
        self.current_app_index = index
        for entry in self.entries.values():
            entry.set_text("")

        # Limpar a lista de capturas de tela
        for row in self.screenshots_list.get_children():
            self.screenshots_list.remove(row)

        if index is not None and 0 <= index < len(self.apps):
            app = self.apps[index]
            for field, entry in self.entries.items():
                entry.set_text(app.get(field, ""))
            for url in app.get("screenshots", []):
                self.add_screenshot_entry(None, url)

        self.notebook.set_current_page(1)

    def edit_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK, text="Por favor, selecione um aplicativo para editar"
            )
            dialog.run()
            dialog.destroy()
            return

        index = model.get_path(treeiter).get_indices()[0]
        self.show_edit_view(index)

    def delete_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK, text="Por favor, selecione um aplicativo para excluir"
            )
            dialog.run()
            dialog.destroy()
            return

        dialog = Gtk.MessageDialog(
            parent=self.window, flags=0, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO, text="Tem certeza que deseja excluir este aplicativo?"
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            index = model.get_path(treeiter).get_indices()[0]
            self.apps.pop(index)
            self.update_treeview()

    def save_app(self, widget):
        app_data = {}
        for field, entry in self.entries.items():
            value = entry.get_text().strip()
            app_data[field] = value

        # Coletar capturas de tela
        app_data["screenshots"] = [row.get_children()[0].get_text().strip() for row in self.screenshots_list.get_children() if row.get_children()[0].get_text().strip()]

        if not app_data["name"]:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK, text="O campo Nome é obrigatório"
            )
            dialog.run()
            dialog.destroy()
            return

        if self.current_app_index is not None and 0 <= self.current_app_index < len(self.apps):
            self.apps[self.current_app_index] = app_data
        else:
            self.apps.append(app_data)

        self.show_list_view()

if __name__ == "__main__":
    app = AppManager()
    Gtk.main()