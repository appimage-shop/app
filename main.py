import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango
import os
import threading
import urllib.request
import json
import shutil
import time
import subprocess

# URL do seu arquivo JSON hospedado no GitHub (substitua esta URL pela sua!)
APPS_DATA_URL = "https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/app.json" 

class AppImageShop(Gtk.Window):
    def __init__(self):
        super().__init__(title="AppImage Shop")
        self.set_default_size(1200, 900)
        self.set_border_width(0)

        # Diretório para AppImages
        self.appimage_dir = os.path.expanduser("~/.local/bin/AppImages")
        os.makedirs(self.appimage_dir, exist_ok=True)

        # Carregar dados de aplicativos da URL externa
        self.apps = [] # Inicializa vazio
        self.load_apps_from_url() # Chama a função para carregar os dados

        # Lista para rastrear downloads
        self.downloads = {} # {app_name: {"progress": float, "status": str}}

        # Estilo CSS para a interface
        self._apply_css()

        # Configuração da UI
        self._setup_ui()
        self.refresh_app_list()

    def _apply_css(self):
        """Aplica estilos CSS para uma interface minimalista e coesa com o tema."""
        css = """
        /* Estilos Gerais para a Janela */
        window {
            background-color: @theme_bg_color; /* Cor de fundo principal do tema */
            color: @theme_text_color;
        }

        /* Header Bar */
        headerbar {
            /* Removido background-color, color e border-bottom para seguir o tema do sistema */
            /* background-color: @theme_selected_bg_color; */
            /* color: @theme_selected_fg_color; */
            /* border-bottom: 1px solid @borders; */
        }
        headerbar .title {
            font-weight: bold;
            color: @theme_selected_fg_color;
        }
        headerbar .subtitle {
            color: alpha(@theme_selected_fg_color, 0.8);
        }

        /* Sidebar (Barra Lateral) */
        .sidebar {
            background-color: @theme_base_color; /* Cor de fundo para superfícies mais elevadas */
            border-right: 1px solid @borders;
            padding: 15px 0;
        }
        .sidebar-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            margin-left: 20px;
            color: @theme_text_color;
        }

        /* Categorias na Sidebar */
        .category-button {
            padding: 10px 20px;
            margin: 2px 10px; /* Margem lateral para espaçamento */
            border-radius: 6px;
            font-size: 1.0em;
            background-color: transparent;
            color: @theme_text_color;
            border: none;
        }
        .category-button:hover {
            background-color: alpha(@theme_selected_bg_color, 0.1); /* Um leve destaque ao passar o mouse */
        }
        .category-button:checked {
            background-color: @theme_selected_bg_color;
            color: @theme_selected_fg_color;
            font-weight: bold;
        }
        .category-frame {
            border: none; /* Remover borda do frame para minimalismo */
            background-color: transparent;
            padding: 0;
        }

        /* Barra de Pesquisa */
        searchentry {
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid @borders;
            background-color: @theme_base_color;
            color: @theme_text_color;
            font-size: 1.0em;
        }
        searchentry:focus {
            border-color: @theme_selected_bg_color;
        }

        /* FlowBox (Cards de Aplicativos) */
        flowboxchild {
            background-color: @theme_base_color;
            border: 1px solid @borders;
            border-radius: 10px;
            padding: 15px;
            margin: 10px;
            box-shadow: none; /* Remover sombra padrão para um look mais flat */
            transition: all 0.2s ease-in-out;
        }
        flowboxchild:hover {
            background-color: alpha(@theme_selected_bg_color, 0.1); /* Leve realce no hover */
            border-color: @theme_selected_bg_color;
        }
        flowboxchild:selected {
            background-color: alpha(@theme_selected_bg_color, 0.2);
            border-color: @theme_selected_bg_color;
        }
        .app-card {
            /* min-width e max-width foram movidos para set_size_request() em Python */
        }
        .app-card .title {
            font-size: 1.1em;
            font-weight: bold;
            color: @theme_text_color;
        }
        .app-card .description {
            font-size: 0.9em;
            color: alpha(@theme_text_color, 0.8);
            margin-top: 5px;
        }
        .app-card .version {
            font-size: 0.85em;
            color: alpha(@theme_text_color, 0.7);
        }

        /* Botões de Ação (Instalar/Remover) */
        button {
            padding: 8px 15px;
            border-radius: 6px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
            border: 1px solid @borders;
        }
        button.suggested-action {
            background-color: @theme_selected_bg_color;
            color: @theme_selected_fg_color;
            border-color: @theme_selected_bg_color;
        }
        button.suggested-action:hover {
            background-color: shade(@theme_selected_bg_color, 0.9); /* Ligeriamente mais escuro */
            border-color: shade(@theme_selected_bg_color, 0.9);
        }
        button.destructive-action {
            background-color: @error_bg_color;
            color: @error_fg_color;
            border-color: @error_bg_color;
        }
        button.destructive-action:hover {
            background-color: shade(@error_bg_color, 0.9);
            border-color: shade(@error_bg_color, 0.9);
        }
        button:not(.suggested-action):not(.destructive-action) { /* Botões padrão */
            background-color: @theme_bg_color;
            color: @theme_text_color;
        }
        button:not(.suggested-action):not(.destructive-action):hover {
            background-color: alpha(@theme_selected_bg_color, 0.1);
        }

        /* Stack Switcher (Abas) */
        stackswitcher button {
            padding: 10px 20px;
            font-size: 1.0em;
            border-radius: 8px;
            background-color: @theme_bg_color;
            color: @theme_text_color;
            border: 1px solid @borders;
        }
        stackswitcher button:checked {
            background-color: @theme_selected_bg_color;
            color: @theme_selected_fg_color;
            font-weight: bold;
            border-color: @theme_selected_bg_color;
        }
        stackswitcher button:hover {
            background-color: alpha(@theme_selected_bg_color, 0.1);
        }

        /* Seção de Detalhes do Aplicativo */
        .details-view {
            padding: 25px;
            background-color: @theme_bg_color;
            color: @theme_text_color;
        }
        .details-view .title {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            color: @theme_text_color;
        }
        .details-label {
            font-weight: bold;
            color: @theme_text_color;
            margin-bottom: 5px;
        }
        .details-text {
            font-size: 0.95em;
            color: alpha(@theme_text_color, 0.9);
            margin-bottom: 15px;
        }
        .dim-label {
            font-size: 0.85em;
            color: alpha(@theme_text_color, 0.7);
        }

        /* Seção de Downloads */
        .download-row {
            padding: 15px 20px;
            margin-bottom: 8px;
            border-radius: 8px;
            border: 1px solid @borders;
            background-color: @theme_base_color;
        }
        .download-row .title {
            font-size: 1.1em;
            font-weight: bold;
            color: @theme_text_color;
        }
        progressbar {
            min-height: 25px; /* Altura mínima para a barra de progresso */
        }
        progressbar trough {
            border-radius: 5px;
            background-color: alpha(@theme_text_color, 0.1);
        }
        progressbar progress {
            border-radius: 5px;
            background-color: @theme_selected_bg_color;
        }
        progressbar text {
            color: @theme_selected_fg_color;
            font-weight: bold;
        }

        /* Diálogos (Notificações, Confirmações) */
        .dialog {
            border-radius: 10px;
            background-color: @theme_bg_color;
            color: @theme_text_color;
            border: 1px solid @borders;
            box-shadow: 0 4px 10px alpha(black, 0.2);
        }
        .dialog label {
            color: @theme_text_color;
        }
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_apps_from_url(self):
        """Carrega a lista de aplicativos de uma URL externa."""
        try:
            with urllib.request.urlopen(APPS_DATA_URL) as url:
                data = json.loads(url.read().decode())
                self.apps = data
            print("Dados de aplicativos carregados com sucesso da URL.")
        except urllib.error.URLError as e:
            print(f"Erro ao carregar dados da URL: {e.reason}. Usando lista vazia.")
            GLib.idle_add(self.show_notification, "Erro ao carregar lista de aplicativos. Verifique sua conexão ou a URL.")
            self.apps = [] # Fallback para lista vazia em caso de erro
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON da URL: {e}. Usando lista vazia.")
            GLib.idle_add(self.show_notification, "Erro ao processar dados de aplicativos. O formato pode estar incorreto.")
            self.apps = []
        except Exception as e:
            print(f"Erro inesperado ao carregar dados: {e}. Usando lista vazia.")
            GLib.idle_add(self.show_notification, f"Erro inesperado: {e}")
            self.apps = []

    def _setup_ui(self):
        """Configura todos os widgets e o layout principal da interface."""
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(self.main_box)

        # Header Bar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.set_title("AppImage Shop")
        self.header_bar.set_subtitle("Sua loja de AppImage - Desde 2025")
        self.set_titlebar(self.header_bar)

        refresh_button = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
        refresh_button.set_tooltip_text("Atualizar lista de aplicativos")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        self.header_bar.pack_start(refresh_button)

        # Sidebar
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.sidebar.set_size_request(200, -1) # Largura fixa para a sidebar
        self.sidebar.get_style_context().add_class("sidebar")
        self.main_box.pack_start(self.sidebar, False, False, 0)

        sidebar_title = Gtk.Label(label="<b>Categorias</b>")
        sidebar_title.set_use_markup(True)
        sidebar_title.set_halign(Gtk.Align.START)
        sidebar_title.get_style_context().add_class("sidebar-title")
        self.sidebar.pack_start(sidebar_title, False, False, 10)

        self.category_group = None
        self.category_buttons = {}
        all_button = Gtk.RadioButton.new_with_label(None, "Todas")
        all_button.set_tooltip_text("Mostrar todos os aplicativos")
        all_button.connect("toggled", self.on_category_toggled, "Todas")
        all_button.get_style_context().add_class("category-button")
        self.sidebar.pack_start(all_button, False, False, 0)
        self.category_group = all_button
        self.category_buttons["Todas"] = all_button

        categories = sorted(set(app["category"] for app in self.apps))
        for category in categories:
            button = Gtk.RadioButton.new_with_label_from_widget(self.category_group, category)
            button.set_tooltip_text(f"Filtrar por {category}")
            button.connect("toggled", self.on_category_toggled, category)
            button.get_style_context().add_class("category-button")
            self.category_buttons[category] = button
            self.sidebar.pack_start(button, False, False, 0)

        # Main Content Area (Stack for different views)
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.main_box.pack_start(self.content_area, True, True, 0)

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_halign(Gtk.Align.CENTER)
        self.stack_switcher.set_margin_top(15)
        self.stack_switcher.get_style_context().add_class("stack-switcher")
        self.content_area.pack_start(self.stack_switcher, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack_switcher.set_stack(self.stack)
        self.content_area.pack_start(self.stack, True, True, 0)

        # Applications View
        self._create_applications_view()

        # Downloads View
        self._create_downloads_view()

        # Accelerator Group (for keyboard shortcuts)
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        self.flow_box.add_accelerator(
            "child-activated", accel_group, Gdk.KEY_Return, 0, Gtk.AccelFlags.VISIBLE
        )

    def _create_applications_view(self):
        """Cria a view principal para exibir os aplicativos."""
        apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.stack.add_titled(apps_box, "apps", "Aplicativos")

        # Search Bar
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_box.set_margin_start(20)
        search_box.set_margin_end(20)
        search_box.set_margin_top(15)
        apps_box.pack_start(search_box, False, False, 0)

        self.search_entry = Gtk.SearchEntry(placeholder_text="Pesquisar aplicativos...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)

        clear_button = Gtk.Button.new_from_icon_name("edit-clear", Gtk.IconSize.BUTTON)
        clear_button.set_tooltip_text("Limpar pesquisa")
        clear_button.connect("clicked", lambda btn: self.search_entry.set_text(""))
        search_box.pack_start(clear_button, False, False, 0)

        # FlowBox for app cards
        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_max_children_per_line(5) # Ajuste para mais cards por linha se a janela permitir
        self.flow_box.set_min_children_per_line(2)
        self.flow_box.set_column_spacing(15)
        self.flow_box.set_row_spacing(15)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flow_box.set_activate_on_single_click(True)
        self.flow_box.connect("child-activated", self.on_app_selected)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_margin_start(20)
        scrolled_window.set_margin_end(20)
        scrolled_window.set_margin_bottom(20)
        scrolled_window.add(self.flow_box)
        apps_box.pack_start(scrolled_window, True, True, 0)

    def _create_downloads_view(self):
        """Cria a view para exibir o progresso dos downloads."""
        downloads_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.stack.add_titled(downloads_box, "downloads", "Downloads")

        downloads_title = Gtk.Label(label="<b>Downloads Ativos</b>")
        downloads_title.set_use_markup(True)
        downloads_title.set_halign(Gtk.Align.START)
        downloads_title.get_style_context().add_class("section-title")
        downloads_title.set_margin_start(20)
        downloads_title.set_margin_top(15)
        downloads_box.pack_start(downloads_title, False, False, 0)

        self.downloads_list = Gtk.ListBox()
        self.downloads_list.set_selection_mode(Gtk.SelectionMode.NONE)
        
        downloads_scrolled = Gtk.ScrolledWindow()
        downloads_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        downloads_scrolled.set_margin_start(20)
        downloads_scrolled.set_margin_end(20)
        downloads_scrolled.set_margin_bottom(20)
        downloads_scrolled.add(self.downloads_list)
        downloads_box.pack_start(downloads_scrolled, True, True, 0)


    def refresh_app_list(self):
        """Atualiza a lista de aplicativos exibidos no FlowBox com base em filtros."""
        for child in self.flow_box.get_children():
            self.flow_box.remove(child)

        search_text = self.search_entry.get_text().lower()
        selected_category = next((cat for cat, btn in self.category_buttons.items() if btn.get_active()), "Todas")

        for app in self.apps:
            matches_category = (selected_category == "Todas" or app["category"] == selected_category)
            matches_search = (not search_text or search_text in app["name"].lower() or search_text in app["description"].lower())

            if matches_category and matches_search:
                self._create_app_card(app)

        self.flow_box.show_all()

    def _create_app_card(self, app):
        """Cria um widget de card individual para um aplicativo."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("app-card")
        card.set_halign(Gtk.Align.CENTER) # Centraliza conteúdo no card
        card.set_size_request(200, -1) # Define uma largura preferencial de 200px para o card

        icon = Gtk.Image.new_from_icon_name(app["icon"], Gtk.IconSize.DIALOG)
        icon.set_margin_top(5)
        card.pack_start(icon, False, False, 0)

        name_label = Gtk.Label(label=app['name'])
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.get_style_context().add_class("title")
        card.pack_start(name_label, False, False, 0)

        version_label = Gtk.Label(label=f"v{app['version']}")
        version_label.set_halign(Gtk.Align.CENTER)
        version_label.get_style_context().add_class("version")
        card.pack_start(version_label, False, False, 0)

        desc_label = Gtk.Label(label=app["description"])
        desc_label.set_line_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_max_width_chars(30)
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.get_style_context().add_class("description")
        card.pack_start(desc_label, True, True, 5) # Expande para preencher espaço

        self.flow_box.add(card)

    def refresh_downloads_list(self):
        """Atualiza a lista de downloads na view de downloads."""
        for child in self.downloads_list.get_children():
            self.downloads_list.remove(child)

        if not self.downloads:
            no_downloads_label = Gtk.Label(label="Nenhum download em andamento.")
            no_downloads_label.get_style_context().add_class("dim-label")
            row = Gtk.ListBoxRow()
            row.add(no_downloads_label)
            self.downloads_list.add(row)
        else:
            for app_name, info in self.downloads.items():
                self._create_download_row(app_name, info)
        self.downloads_list.show_all()

    def _create_download_row(self, app_name, info):
        """Cria uma linha para exibir o progresso de um download."""
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("download-row")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        row.add(box)

        name_label = Gtk.Label(label=app_name)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_hexpand(True)
        name_label.get_style_context().add_class("title")
        box.pack_start(name_label, True, True, 0)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_hexpand(True) # Para a barra de progresso ocupar espaço
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_bar.set_text(info["status"])
        progress_bar.set_fraction(info["progress"])
        progress_bar.set_halign(Gtk.Align.FILL)
        progress_bar.set_hexpand(True)
        progress_box.pack_start(progress_bar, True, True, 0)

        box.pack_start(progress_box, True, True, 0)
        self.downloads_list.add(row)

    # Event Handlers
    def on_search_changed(self, entry):
        self.stack.set_visible_child_name("apps")
        self.header_bar.set_subtitle("Sua loja de AppImage - Desde 2025")
        self.refresh_app_list()

    def on_category_toggled(self, button, category):
        if button.get_active():
            self.stack.set_visible_child_name("apps")
            self.header_bar.set_subtitle("Sua loja de AppImage - Desde 2025")
            self.refresh_app_list()

    def on_refresh_clicked(self, button):
        self.stack.set_visible_child_name("apps")
        self.header_bar.set_subtitle("Sua loja de AppImage - Desde 2025")
        # Recarregar os dados do JSON externo ao clicar em atualizar
        self.load_apps_from_url() 
        self.refresh_app_list()
        self.refresh_downloads_list()

    def on_app_selected(self, flowbox, child):
        # Acessa o widget Gtk.Box dentro do FlowBoxChild
        app_card_content = flowbox.get_child_at_index(child.get_index()).get_children()[0]
        # O nome do aplicativo é o segundo Label dentro do Gtk.Box (índice 1, após o ícone)
        name_label_widget = app_card_content.get_children()[1]
        app_name = name_label_widget.get_label()
        
        app = next((a for a in self.apps if a["name"] == app_name), None)
        if app:
            self.show_app_details(app)

    def show_app_details(self, app):
        """Exibe a view de detalhes para um aplicativo específico."""
        if self.stack.get_child_by_name("details"):
            self.stack.remove(self.stack.get_child_by_name("details"))

        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        details_box.get_style_context().add_class("details-view")
        self.stack.add_titled(details_box, "details", f"Detalhes: {app['name']}")

        # Back button
        back_button = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON)
        back_button.set_tooltip_text("Voltar à lista de aplicativos")
        back_button.connect("clicked", lambda btn: self.stack.set_visible_child_name("apps") or self.header_bar.set_subtitle("Aplicativos para XFCE"))
        back_button.set_halign(Gtk.Align.START)
        back_button.set_margin_start(20)
        back_button.set_margin_top(15)
        details_box.pack_start(back_button, False, False, 0)

        # Content area for details
        content_grid = Gtk.Grid()
        content_grid.set_column_spacing(25)
        content_grid.set_row_spacing(10)
        content_grid.set_margin_start(25)
        content_grid.set_margin_end(25)
        content_grid.set_margin_bottom(25)
        details_box.pack_start(content_grid, True, True, 0)

        # App Icon
        icon = Gtk.Image.new_from_icon_name(app["icon"], Gtk.IconSize.DIALOG)
        content_grid.attach(icon, 0, 0, 1, 3) # row, column, width, height

        # App Name
        name_label = Gtk.Label(label=f"<b>{app['name']}</b>")
        name_label.set_use_markup(True)
        name_label.set_halign(Gtk.Align.START)
        name_label.get_style_context().add_class("title")
        content_grid.attach(name_label, 1, 0, 1, 1)

        # Version
        version_label = Gtk.Label(label=f"<span weight='bold'>Versão:</span> {app['version']}")
        version_label.set_use_markup(True)
        version_label.set_halign(Gtk.Align.START)
        version_label.get_style_context().add_class("details-text")
        content_grid.attach(version_label, 1, 1, 1, 1)

        # Category
        category_label = Gtk.Label(label=f"<span weight='bold'>Categoria:</span> {app['category']}")
        category_label.set_use_markup(True)
        category_label.set_halign(Gtk.Align.START)
        category_label.get_style_context().add_class("details-text")
        content_grid.attach(category_label, 1, 2, 1, 1)

        # Detailed Description
        description_title = Gtk.Label(label="<b>Descrição</b>")
        description_title.set_use_markup(True)
        description_title.set_halign(Gtk.Align.START)
        description_title.get_style_context().add_class("details-label")
        content_grid.attach(description_title, 0, 3, 2, 1) # Full width

        desc_label = Gtk.Label(label=app["details"])
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(80) # Adjust for better text flow
        desc_label.set_halign(Gtk.Align.START)
        desc_label.get_style_context().add_class("details-text")
        content_grid.attach(desc_label, 0, 4, 2, 1) # Full width

        # Screenshots (Placeholder)
        screenshot_label = Gtk.Label(label="Capturas de tela: (Em breve)")
        if app["screenshots"]: # Check if screenshots data exists
             # TODO: Implement a proper image gallery here
            screenshot_label.set_label("Capturas de tela (disponíveis em breve)")

        screenshot_label.set_halign(Gtk.Align.START)
        screenshot_label.get_style_context().add_class("dim-label")
        content_grid.attach(screenshot_label, 0, 5, 2, 1)

        # Action Button (Install/Remove)
        appimage_path = os.path.join(self.appimage_dir, f"{app['name']}.AppImage")
        installed = os.path.exists(appimage_path)
        
        # This button is recreated each time details are shown, reflecting current state
        self.action_button = Gtk.Button(label="Remover" if installed else "Instalar")
        self.action_button.get_style_context().add_class("destructive-action" if installed else "suggested-action")
        self.action_button.set_tooltip_text("Remover aplicativo" if installed else "Instalar aplicativo")
        self.action_button.connect("clicked", self.on_action_clicked, app["name"], app["appimage_url"], installed)
        self.action_button.set_halign(Gtk.Align.END) # Alinha o botão à direita
        self.action_button.set_margin_end(20)
        self.action_button.set_margin_bottom(15)
        details_box.pack_end(self.action_button, False, False, 0) # Pack ao final do details_box


        details_box.show_all()
        self.stack.set_visible_child_name("details")
        self.header_bar.set_subtitle(f"Detalhes: {app['name']}")

    def on_action_clicked(self, button, name, url, installed_status):
        """Manipulador para o clique do botão Instalar/Remover."""
        if installed_status:
            self.confirm_remove(name, button)
        else:
            self.confirm_install(url, name, button)

    def confirm_install(self, url, name, button):
        """Exibe diálogo de confirmação para instalação."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Deseja instalar {name}?"
        )
        dialog.get_style_context().add_class("dialog")
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            button.set_sensitive(False) # Desabilita o botão durante o download
            self.downloads[name] = {"progress": 0.0, "status": "Iniciando..."}
            self.refresh_downloads_list()
            self.stack.set_visible_child_name("downloads") # Mudar para a aba de downloads
            threading.Thread(target=self._download_and_install_appimage, args=(url, name, button)).start()

    def confirm_remove(self, name, button):
        """Exibe diálogo de confirmação para remoção."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Deseja remover {name}?"
        )
        dialog.get_style_context().add_class("dialog")
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            button.set_sensitive(False) # Desabilita o botão durante a remoção
            threading.Thread(target=self._remove_appimage, args=(name, button)).start()
            self.stack.set_visible_child_name("apps") # Voltar para a aba de apps
            self.header_bar.set_subtitle("Sua loja de AppImage - Desde 2025")

    def _download_and_install_appimage(self, url, name, button):
        """Função para baixar e instalar AppImage em uma thread separada."""
        try:
            appimage_path = os.path.join(self.appimage_dir, f"{name}.AppImage")

            def report_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    fraction = min(downloaded / total_size, 1.0)
                    GLib.idle_add(self._update_download_progress, name, fraction, f"Baixando: {int(fraction * 100)}%")
                else:
                    GLib.idle_add(self._update_download_progress, name, 0.0, "Baixando...")

            urllib.request.urlretrieve(url, appimage_path, reporthook=report_hook)
            os.chmod(appimage_path, 0o755) # Tornar executável

            # Criar e instalar .desktop entry para integração no menu
            app_data = next(app for app in self.apps if app["name"] == name)
            desktop_file_content = f"""[Desktop Entry]
Name={name}
Exec={appimage_path}
Type=Application
Icon={app_data['icon']}
Terminal=false
Categories={app_data['app']};"""
            desktop_path = os.path.expanduser(f"~/.local/share/applications/{name}.desktop")
            with open(desktop_path, 'w') as f:
                f.write(desktop_file_content)

            try:
                subprocess.run(["xdg-desktop-menu", "install", desktop_path], check=True, capture_output=True, text=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_msg = f"Erro ao integrar {name} ao menu: {e}"
                if isinstance(e, subprocess.CalledProcessError):
                    error_msg += f"\nDetalhes: {e.stderr}"
                print(error_msg)
                # Removed: GLib.idle_add(self.show_notification, f"Aviso: Não foi possível integrar {name} ao menu do sistema. Você pode precisar fazê-lo manualmente.")


            GLib.idle_add(self._update_download_progress, name, 1.0, "Concluído")
            GLib.idle_add(self.show_notification, f"{name} instalado com sucesso!")
            GLib.idle_add(self.refresh_app_list) # Atualiza a lista de apps (para refletir 'instalado')
            GLib.idle_add(self._update_action_button, button, name, True) # Atualiza o botão 'Instalar' para 'Remover'
            GLib.idle_add(lambda: self.downloads.pop(name, None) and self.refresh_downloads_list()) # Remove da lista de downloads
        except urllib.error.URLError as e:
            error_message = f"Erro de rede ou URL inválida: {e.reason}"
            GLib.idle_add(self._update_download_progress, name, 0.0, f"Erro: {error_message}")
            GLib.idle_add(self.show_notification, f"Erro ao instalar {name}: {error_message}")
            GLib.idle_add(self._update_action_button, button, name, False)
            GLib.idle_add(lambda: self.downloads.pop(name, None) and self.refresh_downloads_list())
        except Exception as e:
            error_message = f"Erro inesperado durante a instalação: {str(e)}"
            GLib.idle_add(self._update_download_progress, name, 0.0, f"Erro: {error_message}")
            GLib.idle_add(self.show_notification, f"Erro ao instalar {name}: {error_message}")
            GLib.idle_add(self._update_action_button, button, name, False)
            GLib.idle_add(lambda: self.downloads.pop(name, None) and self.refresh_downloads_list())

    def _update_download_progress(self, app_name, fraction, status_text):
        """Atualiza o progresso de um download na interface."""
        if app_name in self.downloads:
            self.downloads[app_name]["progress"] = fraction
            self.downloads[app_name]["status"] = status_text
            self.refresh_downloads_list() # Refrash a lista de downloads para refletir o progresso

    def _update_action_button(self, button, app_name, installed):
        """Atualiza o estado (label e estilo) do botão de ação de instalar/remover."""
        button.set_sensitive(True)
        button.set_label("Remover" if installed else "Instalar")
        button.get_style_context().remove_class("suggested-action")
        button.get_style_context().remove_class("destructive-action")
        button.get_style_context().add_class("destructive-action" if installed else "suggested-action")
        # Força a atualização da view de detalhes para que o botão reflita o estado real
        app = next((a for a in self.apps if a["name"] == app_name), None)
        if app:
            GLib.idle_add(self.show_app_details, app)


    def _remove_appimage(self, name, button):
        """Função para remover AppImage e seu .desktop entry em uma thread separada."""
        try:
            appimage_path = os.path.join(self.appimage_dir, f"{name}.AppImage")
            desktop_path = os.path.expanduser(f"~/.local/share/applications/{name}.desktop")

            if os.path.exists(appimage_path):
                os.remove(appimage_path)
            if os.path.exists(desktop_path):
                try:
                    subprocess.run(["xdg-desktop-menu", "uninstall", desktop_path], check=True, capture_output=True, text=True)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    error_msg = f"Erro ao desintegrar {name} do menu: {e}"
                    if isinstance(e, subprocess.CalledProcessError):
                        error_msg += f"\nDetalhes: {e.stderr}"
                    print(error_msg)
                    # Removed: GLib.idle_add(self.show_notification, f"Aviso: Não foi possível desintegrar {name} do menu do sistema. Você pode precisar remover o atalho manualmente.")
                os.remove(desktop_path) # Remover o arquivo .desktop mesmo se a desintegração falhar

            GLib.idle_add(self.show_notification, f"{name} removido com sucesso!")
            GLib.idle_add(self.refresh_app_list) # Atualiza a lista de apps (para refletir 'não instalado')
            GLib.idle_add(self._update_action_button, button, name, False) # Atualiza o botão 'Remover' para 'Instalar'
        except Exception as e:
            # Removed: GLib.idle_add(self.show_notification, f"Erro ao remover {name}: {str(e)}")
            print(f"Erro ao remover {name}: {str(e)}") # Keep print for debugging if needed
            # Se houver um erro, reabilita o botão e tenta manter o estado atual
            GLib.idle_add(self._update_action_button, button, name, True if os.path.exists(appimage_path) else False)


    def show_notification(self, message):
        """Exibe uma notificação ao usuário."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.get_style_context().add_class("dialog")
        dialog.run()
        dialog.destroy()

def main():
    # Verifica o ambiente desktop. A integração do menu é otimizada para XFCE.
    current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
    if 'XFCE' not in current_desktop and 'Xubuntu' not in current_desktop: # Adicionado Xubuntu para cobrir mais casos
        print(f"Aviso: Este aplicativo é otimizado para o ambiente XFCE (detectado: {current_desktop}). A integração do menu pode não funcionar em outros ambientes.")

    win = AppImageShop()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()