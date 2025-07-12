import json
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class AppManager:
    def __init__(self):
        self.apps = []
        self.current_file = "app.json"
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

        # Aba Sobre
        self.create_about_view()

        # Mostrar visão da lista por padrão
        self.show_list_view()

        self.window.show_all()

    def load_json(self):
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
        except Exception as e:
            dialog = Gtk.MessageDialog(
                parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Falha ao carregar {self.current_file}: {str(e)}"
            )
            dialog.run()
            dialog.destroy()

    def save_json(self):
        try:
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
        filter_json = Gtk.FileFilter()
        filter_json.set_name("Arquivos JSON")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_file = dialog.get_filename()
            self.load_json()
            self.update_treeview()
            self.window.set_title(f"Gerenciador de Aplicativos - {self.current_file}")

        dialog.destroy()

    def create_menu_bar(self):
        menu_box = Gtk.Box(spacing=6)
        list_button = Gtk.Button(label="Listar Aplicativos")
        list_button.connect("clicked", lambda w: self.show_list_view())
        menu_box.pack_start(list_button, False, False, 0)

        add_button = Gtk.Button(label="Adicionar Novo Aplicativo")
        add_button.connect("clicked", lambda w: self.show_edit_view(None))
        menu_box.pack_start(add_button, False, False, 0)

        open_button = Gtk.Button(label="Abrir Arquivo")
        open_button.connect("clicked", self.open_file)
        menu_box.pack_start(open_button, False, False, 0)

        save_button = Gtk.Button(label="Salvar Alterações")
        save_button.connect("clicked", lambda w: self.save_json())
        menu_box.pack_start(save_button, False, False, 0)

        about_button = Gtk.Button(label="Sobre")
        about_button.connect("clicked", lambda w: self.notebook.set_current_page(2))
        menu_box.pack_start(about_button, False, False, 0)

        self.box.pack_start(menu_box, False, False, 0)

    def create_list_view(self):
        self.list_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # TreeView
        self.store = Gtk.ListStore(str, str, str)
        self.treeview = Gtk.TreeView(model=self.store)
        for i, column_title in enumerate(["Nome", "Versão", "Categoria"]):
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
            ("Capturas de Tela (separadas por vírgula)", "screenshots")
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

        self.edit_view.pack_start(grid, False, False, 0)

        button_box = Gtk.Box(spacing=6)
        save_button = Gtk.Button(label="Salvar Aplicativo")
        save_button.connect("clicked", self.save_app)
        button_box.pack_start(save_button, False, False, 0)

        cancel_button = Gtk.Button(label="Cancelar")
        cancel_button.connect("clicked", lambda w: self.show_list_view())
        button_box.pack_start(cancel_button, False, False, 0)

        self.edit_view.pack_start(button_box, False, False, 0)
        self.notebook.append_page(self.edit_view, Gtk.Label(label="Editar/Adicionar"))

    def create_about_view(self):
        about_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        about_view.set_border_width(10)

        title_label = Gtk.Label()
        title_label.set_markup("<b>Editor App.json</b>")
        about_view.pack_start(title_label, False, False, 0)

        dev_label = Gtk.Label(label="Desenvolvido por: Mateus Gonçalves")
        about_view.pack_start(dev_label, False, False, 0)

        desc_label = Gtk.Label(label="Um aplicativo para gerenciar arquivos JSON de aplicativos, permitindo adicionar, editar e excluir entradas.")
        desc_label.set_line_wrap(True)
        about_view.pack_start(desc_label, False, False, 0)

        self.notebook.append_page(about_view, Gtk.Label(label="Sobre"))

    def update_treeview(self):
        self.store.clear()
        for app in self.apps:
            self.store.append([app["name"], app["version"], app["category"]])

    def show_list_view(self):
        self.notebook.set_current_page(0)
        self.update_treeview()

    def show_edit_view(self, index):
        self.current_app_index = index
        for entry in self.entries.values():
            entry.set_text("")

        if index is not None and 0 <= index < len(self.apps):
            app = self.apps[index]
            for field, entry in self.entries.items():
                if field == "screenshots":
                    entry.set_text(", ".join(app.get(field, [])))
                else:
                    entry.set_text(app.get(field, ""))

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
            if field == "screenshots":
                app_data[field] = [url.strip() for url in value.split(",") if url.strip()]
            else:
                app_data[field] = value

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