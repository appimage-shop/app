import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango, GdkPixbuf
import os
import threading
import urllib.request
import json
import shutil
import time
import subprocess
import configparser
from urllib.parse import quote
from datetime import datetime

# URL padrão para os dados JSON de AppImage
DEFAULT_APPS_DATA_URL = "https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/app.json"
# URL para o ícone da aplicação
APP_ICON_URL = "https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/icon.png"

class AppImageShop(Gtk.Window):
    """Janela principal do AppImage Shop."""
    def __init__(self):
        super().__init__(title="AppImage Shop")
        self.set_default_size(1200, 900)
        self.set_border_width(0)

        # Diretórios para configuração, downloads, ícones e cache
        self.config_dir = os.path.expanduser("~/.local/share/AppImageShop")
        self.config_file = os.path.join(self.config_dir, "config.ini")
        self.downloads_file = os.path.join(self.config_dir, "downloads.json")
        self.cache_file = os.path.join(self.config_dir, "apps_cache.json")
        os.makedirs(self.config_dir, exist_ok=True)

        # Inicializa configuração e diretórios
        self.config = configparser.ConfigParser()
        self.load_config()
        self.appimage_dir = self.config.get('Downloads', 'appimage_dir')
        self.apps_data_url = self.config.get('Downloads', 'apps_data_url')
        self.icon_dir = os.path.expanduser("~/.local/share/AppImageShop/icons")
        os.makedirs(self.appimage_dir, exist_ok=True)
        os.makedirs(self.icon_dir, exist_ok=True)

        # Define o ícone da janela
        self.set_app_icon()

        # Gerencia downloads e histórico
        self.downloads = {}  # Downloads ativos
        self.download_threads = {}  # Threads para downloads ativos
        self.download_history = self.load_download_history()
        self.apps = []  # Lista de aplicativos disponíveis

        # Aplica CSS e configura UI
        self._apply_css()
        self._setup_ui()

        # Carrega aplicativos e inicia verificação de atualizações se auto_refresh estiver habilitado
        if self.config.getboolean('Settings', 'auto_refresh'):
            self.load_apps_from_url()
            GLib.timeout_add_seconds(int(self.config['Settings']['update_interval']), self.check_for_updates)

    def set_app_icon(self):
        """Define o ícone da janela, baixando de APP_ICON_URL se necessário."""
        icon_path = os.path.join(self.icon_dir, "appimage-shop.png")
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception as e:
                print(f"Erro ao carregar ícone da aplicação: {e}")
                self.set_icon_name("software-install")
        else:
            def load_icon_async():
                try:
                    urllib.request.urlretrieve(APP_ICON_URL, icon_path)
                    GLib.idle_add(lambda: self.set_icon_from_file(icon_path))
                except Exception as e:
                    print(f"Erro ao baixar ícone da aplicação: {e}")
                    GLib.idle_add(lambda: self.set_icon_name("software-install"))

            threading.Thread(target=load_icon_async, daemon=True).start()
            self.set_icon_name("software-install")  # Fallback até o download ser concluído

    # Gerenciamento de Configuração
    def load_config(self):
        """Carrega configuração do config.ini com valores padrão."""
        defaults = {
            'Settings': {'auto_refresh': 'True', 'last_tab': '0', 'last_category': 'Todos', 'update_interval': '3600'},
            'Accessibility': {'high_contrast': 'False', 'font_scale': '1.0'},
            'Appearance': {'theme': 'Sistema'},
            'Downloads': {'appimage_dir': os.path.expanduser("~/.local/bin/AppImages"),
                         'apps_data_url': DEFAULT_APPS_DATA_URL}
        }
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        for section, options in defaults.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in options.items():
                self.config[section].setdefault(key, value)
        # Valida tema
        if self.config['Appearance']['theme'] not in ['Claro', 'Escuro', 'Sistema']:
            self.config['Appearance']['theme'] = 'Sistema'
            self.save_config()

    def save_config(self):
        """Salva configuração no config.ini."""
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def reset_config(self):
        """Redefine configuração para valores padrão."""
        self.load_config()  # Recarrega padrões
        self.appimage_dir = self.config['Downloads']['appimage_dir']
        self.apps_data_url = self.config['Downloads']['apps_data_url']
        os.makedirs(self.appimage_dir, exist_ok=True)
        self._apply_css()
        self.refresh_app_list()
        self.refresh_downloads_list()

    def load_download_history(self):
        """Carrega histórico de downloads do downloads.json."""
        try:
            if os.path.exists(self.downloads_file):
                with open(self.downloads_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar histórico de downloads: {e}")
        return []

    def save_download_history(self):
        """Salva histórico de downloads no downloads.json."""
        try:
            with open(self.downloads_file, 'w') as f:
                json.dump(self.download_history, f, indent=2)
        except IOError as e:
            print(f"Erro ao salvar histórico de downloads: {e}")

    def update_download_history(self, app_name, info):
        """Atualiza histórico de downloads com uma nova entrada ou atualizada."""
        self.download_history = [entry for entry in self.download_history if entry["name"] != app_name]
        self.download_history.append({
            "name": app_name,
            "progress": info["progress"],
            "status": info["status"],
            "timestamp": info.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        })
        self.save_download_history()

    def _apply_css(self):
        """Aplica estilos CSS com base na configuração."""
        high_contrast = self.config.getboolean('Accessibility', 'high_contrast')
        font_scale = self.config.getfloat('Accessibility', 'font_scale')
        theme = self.config.get('Appearance', 'theme')

        # Cores baseadas no tema
        colors = {
            'Claro': {'bg': '#FFFFFF', 'fg': '#000000', 'base': '#F5F5F5', 'sel_bg': '#268BD2', 'sel_fg': '#FFFFFF'},
            'Escuro': {'bg': '#2E2E2E', 'fg': '#FFFFFF', 'base': '#3C3C3C', 'sel_bg': '#4A90D9', 'sel_fg': '#FFFFFF'},
            'Sistema': {'bg': '@theme_bg_color', 'fg': '@theme_fg_color', 'base': '@theme_base_color',
                       'sel_bg': '@theme_selected_bg_color', 'sel_fg': '@theme_selected_fg_color'}
        }
        c = colors.get(theme, colors['Sistema'])
        if high_contrast:
            c = {'bg': '#000000', 'fg': '#FFFFFF', 'base': '#1A1A1A', 'sel_bg': '#FFFFFF', 'sel_fg': '#000000'}

        css = f"""
        window {{ background-color: {c['bg']}; color: {c['fg']}; font-size: {font_scale * 100}%; }}
        headerbar {{ background-color: {c['base']}; padding: 10px 14px; box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15); }}
        headerbar .title {{ font-size: {1.4 * font_scale}em; font-weight: bold; }}
        .sidebar {{ background-color: {c['base']}; border-right: 2px solid {'#FFFFFF' if high_contrast else '@borders'}; padding: 25px 0; }}
        .sidebar-title {{ font-size: {1.4 * font_scale}em; font-weight: bold; margin: 0 0 25px 25px; }}
        .category-button {{ padding: 14px 30px; margin: 6px 15px; border-radius: 10px; font-size: {1.15 * font_scale}em;
                           border: {'2px solid #FFFFFF' if high_contrast else 'none'}; }}
        .category-button:hover {{ background-color: {('#333333' if high_contrast else f"alpha({c['sel_bg']}, 0.2)")}; }}
        .category-button:checked {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; font-weight: bold; }}
        searchentry {{ padding: 12px 18px; border-radius: 12px; border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; background-color: {c['base']}; font-size: {1.15 * font_scale}em; }}
        searchentry:focus {{ border-color: {c['sel_bg']}; }}
        .app-row {{ background-color: {c['base']}; border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; border-radius: 10px; padding: 15px; margin: 10px; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }}
        .app-row:hover {{ background-color: {('#333333' if high_contrast else f"alpha({c['sel_bg']}, 0.1)")}; box-shadow: 0 5px 10px rgba(0,0,0,0.15); }}
        .app-row .title {{ font-size: {1.2 * font_scale}em; font-weight: bold; margin-bottom: 5px; }}
        .app-row .description {{ font-size: {0.95 * font_scale}em; opacity: 0.85; }}
        .app-row .version {{ font-size: {0.9 * font_scale}em; opacity: 0.7; }}
        .app-row .update-badge {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; font-size: {0.85 * font_scale}em; padding: 6px 10px; border-radius: 5px; margin-left: 10px; }}
        button {{ padding: 10px 20px; border-radius: 8px; font-weight: bold; border: {'2px solid #FFFFFF' if high_contrast else 'none'}; }}
        button.suggested-action {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; }}
        button.suggested-action:hover {{ background-color: {'#CCCCCC' if high_contrast else f"shade({c['sel_bg']}, 0.9)"}; }}
        button.destructive-action {{ background-color: {'#FF0000' if high_contrast else '@error_bg_color'}; color: {'#FFFFFF' if high_contrast else '@error_fg_color'}; }}
        button.destructive-action:hover {{ background-color: {'#CC0000' if high_contrast else 'shade(@error_bg_color, -0.1)'}; }}
        notebook {{ background-color: {c['bg']}; border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; border-radius: 10px; padding: 4px; }}
        notebook tab {{ padding: 10px 20px; font-size: 14px; border-radius: 8px 8px 0 0; }}
        notebook tab:checked {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; }}
        .details-view {{ padding: 20px; background-color: {c['bg']}; }}
        .details-view .title {{ font-size: {1.8 * font_scale}em; font-weight: bold; margin-bottom: 10px; }}
        .details-label {{ font-weight: bold; margin-bottom: 5px; }}
        .details-text {{ font-size: {1.1 * font_scale}em; margin-bottom: 20px; }}
        .screenshot-image {{ border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; border-radius: 10px; margin: 10px; }}
        .download-row {{ padding: 15px; margin-bottom: 8px; border-radius: 10px; border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; background-color: {c['base']}; }}
        progressbar {{ min-height: 20px; border-radius: 5px; }}
        progressbar trough {{ background-color: {'#333333' if high_contrast else f"alpha({c['fg']}, 0.15)"}; }}
        progressbar progress {{ background-color: {c['sel_bg']}; }}
        .settings-panel {{ padding: 20px; background-color: {c['base']}; border-radius: 10px; }}
        .settings-label {{ font-weight: bold; font-size: {1.2 * font_scale}em; margin-bottom: 10px; color: {c['fg']}; }}
        .settings-notebook tab {{ padding: 10px 20px; font-size: {1.1 * font_scale}em; border-radius: 5px 5px 0 0; }}
        .settings-notebook tab:checked {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; }}
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _setup_ui(self):
        """Configura o layout principal e widgets da UI."""
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.main_box)

        # Barra de Cabeçalho
        self.header_bar = Gtk.HeaderBar(title="AppImage Shop", subtitle="Sua Loja de AppImage - Desde 2025")
        self.header_bar.set_show_close_button(True)
        self.set_titlebar(self.header_bar)

        refresh_button = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
        refresh_button.set_tooltip_text("Atualizar lista de aplicativos")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        self.header_bar.pack_start(refresh_button)

        settings_button = Gtk.Button.new_from_icon_name("preferences-system", Gtk.IconSize.BUTTON)
        settings_button.set_tooltip_text("Abrir configurações")
        settings_button.connect("clicked", self.on_settings_clicked)
        self.header_bar.pack_end(settings_button)

        # Barra Lateral
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.sidebar.set_size_request(200, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        self.main_box.pack_start(self.sidebar, False, False, 0)

        sidebar_title = Gtk.Label(label="<b>Categorias</b>", use_markup=True)
        sidebar_title.get_style_context().add_class("sidebar-title")
        self.sidebar.pack_start(sidebar_title, False, False, 10)

        self.category_group = None
        self.category_buttons = {}
        all_button = Gtk.RadioButton.new_with_label(None, "Todos")
        all_button.connect("toggled", self.on_category_toggled, "Todos")
        all_button.get_style_context().add_class("category-button")
        self.sidebar.pack_start(all_button, False, False, 0)
        self.category_group = all_button
        self.category_buttons["Todos"] = all_button

        # Área de Conteúdo Principal
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_box.pack_start(self.content_area, True, True, 0)

        self.notebook = Gtk.Notebook()
        self.notebook.connect("switch-page", self.on_notebook_page_switched)
        self.content_area.pack_start(self.notebook, True, True, 10)

        self.store_view = self._create_store_view()
        self.notebook.append_page(self.store_view, Gtk.Label(label="Loja"))

        self.my_apps_box = self._create_my_apps_view()
        self.notebook.append_page(self.my_apps_box, Gtk.Label(label="Meus Apps"))

        self.downloads_box = self._create_downloads_view()
        self.notebook.append_page(self.downloads_box, Gtk.Label(label="Downloads"))

    def _create_store_view(self):
        """Cria a visão da loja com busca e lista de aplicativos."""
        store_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.store_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        store_box.pack_start(self.store_stack, True, True, 0)

        apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin=20)
        apps_box.pack_start(search_box, False, False, 0)

        self.search_entry = Gtk.Entry(placeholder_text="Pesquisar aplicativos ou tags...")
        self.search_entry.connect("changed", self.on_search_changed)
        completion = Gtk.EntryCompletion()
        completion.set_model(self._create_completion_model())
        completion.set_text_column(0)
        self.search_entry.set_completion(completion)
        search_box.pack_start(self.search_entry, True, True, 0)

        clear_button = Gtk.Button.new_from_icon_name("edit-clear", Gtk.IconSize.BUTTON)
        clear_button.set_tooltip_text("Limpar busca")
        clear_button.connect("clicked", lambda btn: self.search_entry.set_text(""))
        search_box.pack_start(clear_button, False, False, 0)

        self.app_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.app_list.connect("row-activated", self.on_app_selected)
        scrolled_window = Gtk.ScrolledWindow(margin_start=20, margin_end=20, margin_bottom=20)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.app_list)
        apps_box.pack_start(scrolled_window, True, True, 0)

        self.store_stack.add_named(apps_box, "apps")
        return store_box

    def _create_my_apps_view(self):
        """Cria a visão para aplicativos instalados."""
        my_apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.my_apps_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        my_apps_box.pack_start(self.my_apps_stack, True, True, 0)

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin=15)
        header = Gtk.Label(label="<b>Aplicativos Instalados</b>", use_markup=True)
        list_box.pack_start(header, False, False, 0)

        self.installed_app_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.installed_app_list.connect("row-activated", self.on_app_selected)
        scrolled = Gtk.ScrolledWindow(margin=10)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.installed_app_list)
        list_box.pack_start(scrolled, True, True, 0)

        self.my_apps_stack.add_named(list_box, "list")
        return my_apps_box

    def _create_downloads_view(self):
        """Cria a visão de downloads com histórico e botão de limpar."""
        downloads_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_start=20, margin_top=15)
        title = Gtk.Label(label="<b>Downloads</b>", use_markup=True)
        header_box.pack_start(title, False, False, 0)

        clear_button = Gtk.Button(label="Limpar Histórico")
        clear_button.set_tooltip_text("Limpar histórico de downloads")
        clear_button.connect("clicked", self.on_clear_history_clicked)
        header_box.pack_end(clear_button, False, False, 0)
        downloads_box.pack_start(header_box, False, False, 0)

        self.downloads_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        scrolled = Gtk.ScrolledWindow(margin_start=20, margin_end=20, margin_bottom=20)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.downloads_list)
        downloads_box.pack_start(scrolled, True, True, 0)

        return downloads_box

    def validate_app_data(self, app):
        """Valida os campos obrigatórios e tipos do JSON de um aplicativo."""
        required_fields = ["name", "description", "appimage_url", "icon_url", "category", "app", "version", "details", "license", "size", "last_updated"]
        optional_fields = ["screenshots", "tags", "alternative_versions"]
        for field in required_fields:
            if field not in app:
                return False, f"Campo '{field}' ausente"
            if not isinstance(app[field], str):
                return False, f"Campo '{field}' deve ser uma string"
        for field in optional_fields:
            if field in app:
                if field == "screenshots" and not isinstance(app[field], list):
                    return False, "Campo 'screenshots' deve ser uma lista"
                if field == "tags" and not isinstance(app[field], list):
                    return False, "Campo 'tags' deve ser uma lista de strings"
                if field == "alternative_versions" and not isinstance(app[field], list):
                    return False, "Campo 'alternative_versions' deve ser uma lista"
        if "screenshots" in app:
            for screenshot in app["screenshots"]:
                if not isinstance(screenshot, dict) or "url" not in screenshot or "caption" not in screenshot:
                    return False, "Cada captura de tela deve ter 'url' e 'caption'"
        return True, ""

    def load_apps_from_url(self):
        """Carrega aplicativos da URL JSON configurada de forma assíncrona com cache."""
        self.header_bar.set_subtitle("Carregando aplicativos...")
        spinner = Gtk.Spinner()
        spinner.start()
        self.header_bar.pack_start(spinner)

        def load_async():
            try:
                with urllib.request.urlopen(self.apps_data_url) as url:
                    data = json.loads(url.read().decode())
                    with open(self.cache_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    GLib.idle_add(self._update_apps, data)
            except urllib.error.URLError as e:
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, 'r') as f:
                        data = json.load(f)
                    GLib.idle_add(self._update_apps, data)
                    GLib.idle_add(self.show_notification, "Carregado do cache devido a falha na rede.")
                else:
                    GLib.idle_add(self.show_error_dialog, f"Falha ao carregar aplicativos: {e.reason}", True)
            except json.JSONDecodeError as e:
                GLib.idle_add(self.show_error_dialog, f"Dados de aplicativo inválidos: {e}", False)
            finally:
                GLib.idle_add(spinner.stop)
                GLib.idle_add(self.header_bar.remove, spinner)
                GLib.idle_add(self.header_bar.set_subtitle, "Sua Loja de AppImage - Desde 2025")

        threading.Thread(target=load_async, daemon=True).start()

    def _update_apps(self, data):
        """Atualiza a lista de aplicativos com validação e atualiza a UI."""
        valid_apps = []
        for app in data:
            is_valid, error = self.validate_app_data(app)
            if is_valid:
                valid_apps.append(app)
            else:
                print(f"Aplicativo inválido: {error}")
        self.apps = valid_apps
        self._setup_category_buttons()
        self.refresh_app_list()
        self.notebook.set_current_page(self.config.getint('Settings', 'last_tab'))

    def check_for_updates(self):
        """Verifica periodicamente por atualizações do JSON."""
        if self.config.getboolean('Settings', 'auto_refresh'):
            self.load_apps_from_url()
            return GLib.timeout_add_seconds(int(self.config['Settings']['update_interval']), self.check_for_updates)
        return False

    def _setup_category_buttons(self):
        """Configura botões de categoria na barra lateral."""
        for category, button in list(self.category_buttons.items()):
            if category != "Todos":
                self.sidebar.remove(button)
                del self.category_buttons[category]

        categories = sorted(set(app["category"] for app in self.apps))
        for category in categories:
            button = Gtk.RadioButton.new_with_label_from_widget(self.category_group, category)
            button.connect("toggled", self.on_category_toggled, category)
            button.get_style_context().add_class("category-button")
            self.category_buttons[category] = button
            self.sidebar.pack_start(button, False, False, 0)
        self.sidebar.show_all()

    def refresh_app_list(self):
        """Atualiza a lista de aplicativos com base em filtros de busca e categoria."""
        for child in self.app_list.get_children():
            self.app_list.remove(child)

        search_text = self.search_entry.get_text().lower()
        selected_category = next((cat for cat, btn in self.category_buttons.items() if btn.get_active()), "Todos")

        for app in self.apps:
            if (selected_category == "Todos" or app["category"] == selected_category) and \
               (not search_text or search_text in app["name"].lower() or search_text in app["description"].lower() or
                any(search_text in tag.lower() for tag in app.get("tags", []))):
                self._create_app_row(app, self.app_list)

        self.app_list.show_all()
        self.refresh_my_apps_list()

    def refresh_my_apps_list(self):
        """Atualiza a lista de aplicativos instalados."""
        self.my_apps_stack.set_visible_child_name("list")
        for child in self.installed_app_list.get_children():
            self.installed_app_list.remove(child)

        installed_apps = [app for app in self.apps if os.path.exists(os.path.join(self.appimage_dir, f"{app['name']}.AppImage"))]
        if not installed_apps:
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            empty_box.get_style_context().add_class("app-row")
            empty_icon = Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.DIALOG)
            empty_label = Gtk.Label(label="Nenhum aplicativo instalado.")
            explore_button = Gtk.Button(label="Explorar Loja")
            explore_button.set_tooltip_text("Voltar para a aba Loja")
            explore_button.connect("clicked", lambda btn: self.notebook.set_current_page(0))
            empty_box.pack_start(empty_icon, False, False, 0)
            empty_box.pack_start(empty_label, False, False, 0)
            empty_box.pack_start(explore_button, False, False, 0)
            self.installed_app_list.add(empty_box)
        else:
            for app in installed_apps:
                appimage_path = os.path.join(self.appimage_dir, f"{app['name']}.AppImage")
                desktop_path = os.path.expanduser(f"~/.local/share/applications/{app['name']}.desktop")
                is_update = False
                if os.path.exists(desktop_path):
                    with open(desktop_path, 'r') as f:
                        installed_version = next((line.split("Versão:")[1].strip() for line in f if line.startswith("Comment=Versão:")), app['version'])
                        is_update = installed_version != app['version']
                self._create_app_row(app, self.installed_app_list, is_update)
        self.installed_app_list.show_all()

    def refresh_downloads_list(self):
        """Atualiza a lista de downloads com downloads ativos e histórico."""
        for child in self.downloads_list.get_children():
            self.downloads_list.remove(child)

        all_downloads = {**{entry["name"]: entry for entry in self.download_history}, **self.downloads}
        if not all_downloads:
            self.downloads_list.add(Gtk.Label(label="Nenhum download no histórico."))
        else:
            for app_name in sorted(all_downloads, key=lambda x: all_downloads[x]["timestamp"], reverse=True):
                self._create_download_row(app_name, all_downloads[app_name])
        self.downloads_list.show_all()

    def _create_app_row(self, app, list_box, is_update=False):
        """Cria uma linha de aplicativo para a lista."""
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("app-row")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin=8)
        row.add(box)

        icon = self.get_custom_icon(app)
        box.pack_start(icon, False, False, 0)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)
        box.pack_start(content_box, True, True, 0)

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        name_label = Gtk.Label(label=app['name'], halign=Gtk.Align.START, ellipsize=Pango.EllipsizeMode.END)
        name_label.get_style_context().add_class("title")
        name_box.pack_start(name_label, False, False, 0)
        
        if is_update:
            update_badge = Gtk.Label(label="Atualização")
            update_badge.get_style_context().add_class("update-badge")
            name_box.pack_start(update_badge, False, False, 0)
        content_box.pack_start(name_box, False, False, 0)

        version_label = Gtk.Label(label=f"v{app.get('version', 'N/A')} ({app.get('size', 'N/A')})", halign=Gtk.Align.START)
        version_label.get_style_context().add_class("version")
        content_box.pack_start(version_label, False, False, 0)

        desc_label = Gtk.Label(label=app.get("description", "Sem descrição"), wrap=True, halign=Gtk.Align.START, max_width_chars=60)
        desc_label.get_style_context().add_class("description")
        content_box.pack_start(desc_label, False, False, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        appimage_path = os.path.join(self.appimage_dir, f"{app['name']}.AppImage")
        action_button = Gtk.Button(label="Remover" if os.path.exists(appimage_path) else "Instalar")
        action_button.get_style_context().add_class("destructive-action" if os.path.exists(appimage_path) else "suggested-action")
        action_button.connect("clicked", self.on_action_clicked, app["name"], app.get("appimage_url", ""), os.path.exists(appimage_path), app.get("version"))
        button_box.pack_start(action_button, False, False, 0)

        if os.path.exists(appimage_path):
            launch_button = Gtk.Button(label="Iniciar")
            launch_button.get_style_context().add_class("suggested-action")
            launch_button.connect("clicked", self.on_launch_clicked, app["name"])
            button_box.pack_start(launch_button, False, False, 0)

        box.pack_end(button_box, False, False, 0)
        list_box.add(row)

    def _create_download_row(self, app_name, info):
        """Cria uma linha de progresso de download."""
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("download-row")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin=5)
        row.add(box)

        status_icon = Gtk.Image.new_from_icon_name("dialog-error" if "Erro" in info["status"] else "emblem-downloads", Gtk.IconSize.BUTTON)
        box.pack_start(status_icon, False, False, 0)

        name_label = Gtk.Label(label=app_name, halign=Gtk.Align.START, hexpand=True)
        name_label.get_style_context().add_class("title")
        box.pack_start(name_label, True, True, 0)

        status_text = info["status"].replace("Downloading", "Baixando").replace("Completed", "Concluído").replace("Error", "Erro").replace("Canceling", "Cancelando").replace("Canceled", "Cancelado")
        progress_bar = Gtk.ProgressBar(show_text=True, text=f"{status_text} ({info['timestamp']})", fraction=info["progress"])
        box.pack_start(progress_bar, True, True, 0)

        if app_name in self.download_threads:
            cancel_button = Gtk.Button.new_from_icon_name("process-stop", Gtk.IconSize.BUTTON)
            cancel_button.set_tooltip_text("Cancelar download")
            cancel_button.connect("clicked", self.on_cancel_download, app_name)
            box.pack_end(cancel_button, False, False, 0)

        self.downloads_list.add(row)

    def get_custom_icon(self, app):
        """Carrega ou busca um ícone de aplicativo de forma assíncrona."""
        icon = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
        icon_url = app.get("icon_url")
        if not icon_url:
            return icon

        icon_path = os.path.join(self.icon_dir, f"{quote(app['name'])}.png")
        if os.path.exists(icon_path):
            try:
                icon.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 64, 64))
            except Exception as e:
                print(f"Erro ao carregar ícone para {app['name']}: {e}")
            return icon

        def load_icon_async():
            try:
                urllib.request.urlretrieve(icon_url, icon_path)
                GLib.idle_add(lambda: icon.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 64, 64)))
            except Exception as e:
                print(f"Erro ao baixar ícone para {app['name']}: {e}")

        threading.Thread(target=load_icon_async, daemon=True).start()
        return icon

    def get_screenshot_image(self, screenshot, app_name):
        """Carrega ou busca uma captura de tela de forma assíncrona."""
        image = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
        screenshot_url = screenshot.get("url")
        screenshot_path = os.path.join(self.icon_dir, f"{quote(app_name)}_screenshot_{quote(screenshot_url.split('/')[-1])}")
        if os.path.exists(screenshot_path):
            try:
                image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(screenshot_path, 400, 300))
            except Exception as e:
                print(f"Erro ao carregar captura de tela para {app_name}: {e}")
            return image

        def load_screenshot_async():
            try:
                urllib.request.urlretrieve(screenshot_url, screenshot_path)
                GLib.idle_add(lambda: image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(screenshot_path, 400, 300)))
            except Exception as e:
                print(f"Erro ao baixar captura de tela para {app_name}: {e}")

        threading.Thread(target=load_screenshot_async, daemon=True).start()
        return image

    def on_search_changed(self, entry):
        """Manipula mudanças no campo de busca."""
        self.notebook.set_current_page(0)
        self.store_stack.set_visible_child_name("apps")
        self.header_bar.set_subtitle("Sua Loja de AppImage - Desde 2025")
        self.refresh_app_list()

    def on_category_toggled(self, button, category):
        """Manipula seleção de categoria."""
        if button.get_active():
            self.notebook.set_current_page(0)
            self.store_stack.set_visible_child_name("apps")
            self.header_bar.set_subtitle("Sua Loja de AppImage - Desde 2025")
            self.config['Settings']['last_category'] = category
            self.save_config()
            self.refresh_app_list()

    def on_refresh_clicked(self, button):
        """Manipula clique no botão de atualizar."""
        self.notebook.set_current_page(0)
        self.store_stack.set_visible_child_name("apps")
        self.header_bar.set_subtitle("Sua Loja de AppImage - Desde 2025")
        self.load_apps_from_url()

    def on_notebook_page_switched(self, notebook, page, page_num):
        """Salva a aba selecionada do notebook."""
        self.config['Settings']['last_tab'] = str(page_num)
        self.save_config()

    def on_clear_history_clicked(self, button):
        """Limpa o histórico de downloads."""
        self.download_history = []
        self.downloads.clear()
        self.download_threads.clear()
        self.save_download_history()
        self.refresh_downloads_list()

    def on_cancel_download(self, button, app_name):
        """Cancela um download ativo."""
        button.set_sensitive(False)
        spinner = Gtk.Spinner()
        spinner.start()
        button.add(spinner)
        if app_name in self.download_threads:
            self.download_threads[app_name].cancelled = True
            self.downloads[app_name]["status"] = "Cancelando..."
            self.downloads[app_name]["progress"] = 0.0
            self.refresh_downloads_list()
            GLib.timeout_add(500, self._complete_cancel, app_name, button, spinner)

    def _complete_cancel(self, app_name, button, spinner):
        """Conclui o cancelamento de um download."""
        self.downloads[app_name]["status"] = "Cancelado"
        self.downloads[app_name]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_download_history(app_name, self.downloads[app_name])
        self.refresh_downloads_list()
        button.remove(spinner)
        button.set_sensitive(True)
        del self.download_threads[app_name]
        self.show_notification(f"Download de {app_name} cancelado.")
        return False

    def on_settings_clicked(self, button):
        """Abre o diálogo de configurações."""
        dialog = Gtk.Dialog(title="Configurações", transient_for=self, modal=True)
        dialog.set_default_size(500, 400)
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Aplicar", Gtk.ResponseType.APPLY)
        content_area = dialog.get_content_area()
        content_area.set_border_width(15)

        notebook = Gtk.Notebook()
        content_area.pack_start(notebook, True, True, 0)

        # Aba de Acessibilidade
        accessibility_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=15)
        accessibility_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        accessibility_box.pack_start(accessibility_grid, False, False, 0)

        high_contrast_label = Gtk.Label(label="Alto Contraste", halign=Gtk.Align.START)
        high_contrast_label.get_style_context().add_class("settings-label")
        high_contrast_switch = Gtk.Switch(halign=Gtk.Align.END, active=self.config.getboolean('Accessibility', 'high_contrast'))
        accessibility_grid.attach(high_contrast_label, 0, 0, 1, 1)
        accessibility_grid.attach(high_contrast_switch, 1, 0, 1, 1)

        font_scale_label = Gtk.Label(label="Escala de Fonte", halign=Gtk.Align.START)
        font_scale_label.get_style_context().add_class("settings-label")
        font_scale_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment(value=float(self.config.get('Accessibility', 'font_scale')), lower=0.8, upper=1.5, step_increment=0.1), digits=1)
        font_scale_spin.set_tooltip_text("Definir tamanho da fonte (0.8 a 1.5)")
        accessibility_grid.attach(font_scale_label, 0, 1, 1, 1)
        accessibility_grid.attach(font_scale_spin, 1, 1, 1, 1)

        theme_label = Gtk.Label(label="Tema", halign=Gtk.Align.START)
        theme_label.get_style_context().add_class("settings-label")
        theme_combo = Gtk.ComboBoxText()
        for theme in ["Claro", "Escuro", "Sistema"]:
            theme_combo.append_text(theme)
        theme_combo.set_active(["Claro", "Escuro", "Sistema"].index(self.config.get('Appearance', 'theme')))
        accessibility_grid.attach(theme_label, 0, 2, 1, 1)
        accessibility_grid.attach(theme_combo, 1, 2, 1, 1)

        notebook.append_page(accessibility_box, Gtk.Label(label="Acessibilidade"))

        # Aba de Downloads
        downloads_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=15)
        downloads_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        downloads_box.pack_start(downloads_grid, False, False, 0)

        appimage_dir_label = Gtk.Label(label="Diretório de AppImage", halign=Gtk.Align.START)
        appimage_dir_label.get_style_context().add_class("settings-label")
        appimage_dir_chooser = Gtk.FileChooserButton(title="Selecionar Diretório de AppImage", action=Gtk.FileChooserAction.SELECT_FOLDER)
        appimage_dir_chooser.set_filename(self.config.get('Downloads', 'appimage_dir'))
        downloads_grid.attach(appimage_dir_label, 0, 0, 1, 1)
        downloads_grid.attach(appimage_dir_chooser, 1, 0, 1, 1)

        apps_data_url_label = Gtk.Label(label="URL do JSON de Aplicativos", halign=Gtk.Align.START)
        apps_data_url_label.get_style_context().add_class("settings-label")
        apps_data_url_entry = Gtk.Entry(text=self.config.get('Downloads', 'apps_data_url'))
        apps_data_url_entry.set_placeholder_text("Insira a URL do arquivo app.json")
        downloads_grid.attach(apps_data_url_label, 0, 1, 1, 1)
        downloads_grid.attach(apps_data_url_entry, 1, 1, 1, 1)

        notebook.append_page(downloads_box, Gtk.Label(label="Downloads"))

        # Aba Geral
        general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=15)
        general_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        general_box.pack_start(general_grid, False, False, 0)

        auto_refresh_label = Gtk.Label(label="Atualização Automática", halign=Gtk.Align.START)
        auto_refresh_label.get_style_context().add_class("settings-label")
        auto_refresh_switch = Gtk.Switch(halign=Gtk.Align.END, active=self.config.getboolean('Settings', 'auto_refresh'))
        general_grid.attach(auto_refresh_label, 0, 0, 1, 1)
        general_grid.attach(auto_refresh_switch, 1, 0, 1, 1)

        update_interval_label = Gtk.Label(label="Intervalo de Atualização (segundos)", halign=Gtk.Align.START)
        update_interval_label.get_style_context().add_class("settings-label")
        update_interval_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment(value=float(self.config.get('Settings', 'update_interval')), lower=300, upper=86400, step_increment=300), digits=0)
        update_interval_spin.set_tooltip_text("Definir intervalo de atualização (300 a 86400 segundos)")
        general_grid.attach(update_interval_label, 0, 1, 1, 1)
        general_grid.attach(update_interval_spin, 1, 1, 1, 1)

        reset_button = Gtk.Button(label="Redefinir Configurações")
        reset_button.get_style_context().add_class("destructive-action")
        reset_button.set_tooltip_text("Redefinir todas as configurações para o padrão")
        reset_button.connect("clicked", self.on_reset_settings_clicked)
        general_grid.attach(reset_button, 1, 2, 1, 1)

        notebook.append_page(general_box, Gtk.Label(label="Geral"))

        # Aba Sobre
        about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=15)
        about_label = Gtk.Label(
            label="<b>AppImage Shop</b>\nUma loja para descobrir, baixar e gerenciar aplicativos AppImage.\n\n<b>Desenvolvedor:</b> Mateus Gonçalves\n\n<b>Licença:</b> GPL-3.0",
            use_markup=True, justify=Gtk.Justification.CENTER
        )
        about_label.get_style_context().add_class("settings-label")
        about_box.pack_start(about_label, False, False, 0)
        notebook.append_page(about_box, Gtk.Label(label="Sobre"))

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.APPLY:
            confirm_dialog = Gtk.MessageDialog(transient_for=dialog, message_type=Gtk.MessageType.QUESTION,
                                              buttons=Gtk.ButtonsType.YES_NO, text="Aplicar alterações?")
            if confirm_dialog.run() == Gtk.ResponseType.YES:
                self.config['Accessibility']['high_contrast'] = str(high_contrast_switch.get_active())
                self.config['Accessibility']['font_scale'] = str(font_scale_spin.get_value())
                self.config['Appearance']['theme'] = theme_combo.get_active_text()
                self.config['Downloads']['appimage_dir'] = appimage_dir_chooser.get_filename()
                self.config['Downloads']['apps_data_url'] = apps_data_url_entry.get_text() or DEFAULT_APPS_DATA_URL
                self.config['Settings']['auto_refresh'] = str(auto_refresh_switch.get_active())
                self.config['Settings']['update_interval'] = str(int(update_interval_spin.get_value()))
                self.save_config()
                self.appimage_dir = self.config.get('Downloads', 'appimage_dir')
                self.apps_data_url = self.config.get('Downloads', 'apps_data_url')
                os.makedirs(self.appimage_dir, exist_ok=True)
                self._apply_css()
                self.refresh_app_list()
                self.refresh_downloads_list()
                self.load_apps_from_url()
            confirm_dialog.destroy()
        dialog.destroy()

    def on_reset_settings_clicked(self, button):
        """Manipula clique no botão de redefinir configurações."""
        confirm_dialog = Gtk.MessageDialog(transient_for=button.get_toplevel(), message_type=Gtk.MessageType.WARNING,
                                          buttons=Gtk.ButtonsType.YES_NO, text="Redefinir todas as configurações para o padrão?")
        confirm_dialog.format_secondary_text("Isso não afetará aplicativos instalados ou histórico de downloads.")
        if confirm_dialog.run() == Gtk.ResponseType.YES:
            self.reset_config()
            self.show_notification("Configurações redefinidas para o padrão.")
        confirm_dialog.destroy()

    def on_app_selected(self, listbox, row):
        """Manipula seleção de aplicativo no ListBox."""
        if row and row.get_child():
            box = row.get_child()
            children = box.get_children()
            if len(children) >= 2 and isinstance(children[1], Gtk.Box):  # Check if content_box exists
                content_box = children[1]
                name_box = content_box.get_children()[0]  # First child is name_box
                name_label = name_box.get_children()[0]  # First child is name_label
                if isinstance(name_label, Gtk.Label):
                    app_name = name_label.get_label()
                    app = next((a for a in self.apps if a["name"] == app_name), None)
                    if app:
                        print(f"App selecionado: {app_name}, Detalhes: {app}")
                        if listbox == self.installed_app_list:
                            self.notebook.set_current_page(1)
                            self.show_app_details(app, self.my_apps_stack, "list")
                        else:
                            self.notebook.set_current_page(0)
                            self.show_app_details(app, self.store_stack, "apps")
                    else:
                        print(f"Aplicativo não encontrado: {app_name}")
                else:
                    print("Name label not found in row structure")
            else:
                print("Invalid row structure or placeholder row selected")

    def show_app_details(self, app, target_stack, back_view_name):
        """Exibe a visão detalhada do aplicativo."""
        details_name = f"details_{app['name']}"
        if target_stack.get_child_by_name(details_name):
            target_stack.remove(target_stack.get_child_by_name(details_name))

        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        details_box.get_style_context().add_class("details-view")
        details_box.set_property("visible", True)

        back_button = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON)
        back_button.set_tooltip_text("Voltar para a lista")
        back_button.connect("clicked", lambda btn: [target_stack.set_visible_child_name(back_view_name),
                                                   self.header_bar.set_subtitle("Sua Loja de AppImage - Desde 2025")])
        details_box.pack_start(back_button, False, False, 0)

        content_grid = Gtk.Grid(column_spacing=15, row_spacing=5, margin=10)
        content_grid.set_property("visible", True)
        details_box.pack_start(content_grid, True, True, 0)

        icon = self.get_custom_icon(app)
        icon.set_property("visible", True)
        content_grid.attach(icon, 0, 0, 1, 4)

        name_label = Gtk.Label(label=f"<b>{app['name']}</b>", use_markup=True, halign=Gtk.Align.START)
        name_label.get_style_context().add_class("title")
        name_label.set_property("visible", True)
        content_grid.attach(name_label, 1, 0, 1, 1)

        version_label = Gtk.Label(label=f"<b>Versão:</b> {app.get('version', 'N/A')} ({app.get('size', 'N/A')})", use_markup=True, halign=Gtk.Align.START)
        version_label.get_style_context().add_class("details-text")
        version_label.set_property("visible", True)
        content_grid.attach(version_label, 1, 1, 1, 1)

        category_label = Gtk.Label(label=f"<b>Categoria:</b> {app.get('category', 'N/A')}", use_markup=True, halign=Gtk.Align.START)
        category_label.get_style_context().add_class("details-text")
        category_label.set_property("visible", True)
        content_grid.attach(category_label, 1, 2, 1, 1)

        license_label = Gtk.Label(label=f"<b>Licença:</b> {app.get('license', 'N/A')}", use_markup=True, halign=Gtk.Align.START)
        license_label.get_style_context().add_class("details-text")
        license_label.set_property("visible", True)
        content_grid.attach(license_label, 1, 3, 1, 1)

        last_updated_label = Gtk.Label(label=f"<b>Última Atualização:</b> {app.get('last_updated', 'N/A')}", use_markup=True, halign=Gtk.Align.START)
        last_updated_label.get_style_context().add_class("details-text")
        last_updated_label.set_property("visible", True)
        content_grid.attach(last_updated_label, 1, 4, 1, 1)

        tags_label = Gtk.Label(label=f"<b>Tags:</b> {', '.join(app.get('tags', [])) or 'N/A'}", use_markup=True, halign=Gtk.Align.START)
        tags_label.get_style_context().add_class("details-text")
        tags_label.set_property("visible", True)
        content_grid.attach(tags_label, 1, 5, 1, 1)

        description_title = Gtk.Label(label="<b>Descrição</b>", use_markup=True, halign=Gtk.Align.START)
        description_title.get_style_context().add_class("details-label")
        description_title.set_property("visible", True)
        content_grid.attach(description_title, 0, 6, 2, 1)

        desc_label = Gtk.Label(label=app.get("details", "Sem descrição disponível"), wrap=True, max_width_chars=80, halign=Gtk.Align.START)
        desc_label.get_style_context().add_class("details-text")
        desc_label.set_property("visible", True)
        content_grid.attach(desc_label, 0, 7, 2, 1)

        screenshot_label = Gtk.Label(label="<b>Capturas de Tela</b>", use_markup=True, halign=Gtk.Align.START)
        screenshot_label.get_style_context().add_class("details-label")
        screenshot_label.set_property("visible", True)
        content_grid.attach(screenshot_label, 0, 8, 2, 1)

        screenshots = app.get("screenshots", [])
        if screenshots:
            screenshot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            screenshot_box.set_property("visible", True)
            for screenshot in screenshots[:3]:
                image = self.get_screenshot_image(screenshot, app["name"])
                image.set_property("visible", True)
                caption_label = Gtk.Label(label=screenshot.get("caption", "Sem legenda"), wrap=True, halign=Gtk.Align.CENTER)
                caption_label.get_style_context().add_class("details-text")
                caption_label.set_property("visible", True)
                screenshot_box.pack_start(image, False, False, 0)
                screenshot_box.pack_start(caption_label, False, False, 0)
            content_grid.attach(screenshot_box, 0, 9, 2, 1)
        else:
            screenshot_placeholder = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
            screenshot_placeholder.set_property("visible", True)
            content_grid.attach(screenshot_placeholder, 0, 9, 2, 1)

        appimage_path = os.path.join(self.appimage_dir, f"{app['name']}.AppImage")
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.END, margin_end=10, margin_bottom=10)
        button_box.set_property("visible", True)
        details_box.pack_end(button_box, False, False, 0)

        version_combo = Gtk.ComboBoxText()
        version_combo.append_text(f"{app['version']} ({app.get('size', 'N/A')})")
        for alt_version in app.get("alternative_versions", []):
            version_combo.append_text(f"{alt_version['version']} ({alt_version.get('size', 'N/A')})")
        version_combo.set_active(0)
        version_combo.set_property("visible", True)
        button_box.pack_start(version_combo, False, False, 0)

        self.action_button = Gtk.Button(label="Remover" if os.path.exists(appimage_path) else "Instalar")
        self.action_button.get_style_context().add_class("destructive-action" if os.path.exists(appimage_path) else "suggested-action")
        self.action_button.connect("clicked", self.on_action_clicked, app["name"], app.get("appimage_url", ""), os.path.exists(appimage_path), app.get("version"), version_combo)
        self.action_button.set_property("visible", True)
        button_box.pack_start(self.action_button, False, False, 0)

        if os.path.exists(appimage_path):
            launch_button = Gtk.Button(label="Iniciar")
            launch_button.get_style_context().add_class("suggested-action")
            launch_button.connect("clicked", self.on_launch_clicked, app["name"])
            launch_button.set_property("visible", True)
            button_box.pack_start(launch_button, False, False, 0)

        target_stack.add_named(details_box, details_name)
        target_stack.set_visible_child_name(details_name)
        self.header_bar.set_subtitle(f"{app['name']} - Detalhes")
        details_box.show_all()

    def on_launch_clicked(self, button, app_name):
        """Inicia um aplicativo instalado."""
        appimage_path = os.path.join(self.appimage_dir, f"{app_name}.AppImage")
        try:
            subprocess.Popen([appimage_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.show_notification(f"{app_name} iniciado.")
        except Exception as e:
            self.show_notification(f"Erro ao iniciar {app_name}: {e}")

    def on_action_clicked(self, button, name, url, installed, version, version_combo):
        """Manipula clique no botão de instalar/remover."""
        selected_version = version_combo.get_active_text().split(" (")[0]
        app = next((a for a in self.apps if a["name"] == name), None)
        if selected_version != version:
            for alt_version in app.get("alternative_versions", []):
                if alt_version["version"] == selected_version:
                    url = alt_version["appimage_url"]
                    version = alt_version["version"]
                    break

        if installed:
            dialog = Gtk.MessageDialog(transient_for=self, message_type=Gtk.MessageType.QUESTION,
                                      buttons=Gtk.ButtonsType.YES_NO, text=f"Remover {name}?")
            if dialog.run() == Gtk.ResponseType.YES:
                button.set_sensitive(False)
                threading.Thread(target=self._remove_appimage, args=(name, button), daemon=True).start()
                self.store_stack.set_visible_child_name("apps")
                self.my_apps_stack.set_visible_child_name("list")
                self.notebook.set_current_page(0)
                self.header_bar.set_subtitle("Sua Loja de AppImage - Desde 2025")
            dialog.destroy()
        else:
            if not url:
                self.show_notification(f"Nenhuma URL de download disponível para {name}.")
                return
            dialog = Gtk.MessageDialog(transient_for=self, message_type=Gtk.MessageType.QUESTION,
                                      buttons=Gtk.ButtonsType.YES_NO, text=f"Instalar {name} (v{selected_version})?")
            if dialog.run() == Gtk.ResponseType.YES:
                button.set_sensitive(False)
                self.downloads[name] = {"progress": 0.0, "status": "Iniciando...", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                self.update_download_history(name, self.downloads[name])
                self.refresh_downloads_list()
                self.notebook.set_current_page(2)
                thread = threading.Thread(target=self._download_and_install_appimage, args=(url, name, button, version), daemon=True)
                thread.cancelled = False
                self.download_threads[name] = thread
                thread.start()
            dialog.destroy()

    def _download_and_install_appimage(self, url, name, button, version):
        """Baixa e instala um AppImage."""
        appimage_path = os.path.join(self.appimage_dir, f"{name}.AppImage")
        try:
            def report_hook(block_num, block_size, total_size):
                if hasattr(self.download_threads[name], 'cancelled') and self.download_threads[name].cancelled:
                    raise Exception("Download cancelado pelo usuário")
                fraction = min(block_num * block_size / total_size, 1.0) if total_size > 0 else 0.0
                status = f"Baixando: {int(fraction * 100)}%" if total_size > 0 else "Baixando..."
                GLib.idle_add(self._update_download_progress, name, fraction, status)

            urllib.request.urlretrieve(url, appimage_path, reporthook=report_hook)
            os.chmod(appimage_path, 0o755)

            app_data = next(app for app in self.apps if app["name"] == name)
            desktop_file_content = f"""[Desktop Entry]
Name={name}
Exec={appimage_path} %U
Type=Application
Icon={os.path.join(self.icon_dir, f"{quote(name)}.png")}
Terminal=false
Categories={app_data['app']};
Comment=Versão: {version}"""
            desktop_path = os.path.expanduser(f"~/.local/share/applications/{name}.desktop")
            with open(desktop_path, 'w') as f:
                f.write(desktop_file_content)

            GLib.idle_add(self._update_download_progress, name, 1.0, "Concluído")
            GLib.idle_add(self.show_notification, f"{name} (v{version}) instalado com sucesso!")
            GLib.idle_add(self.refresh_app_list)
            GLib.idle_add(self._update_action_button, button, name, True)
            GLib.idle_add(lambda: self.downloads.pop(name, None) and self.download_threads.pop(name, None) and self.refresh_downloads_list())
        except Exception as e:
            GLib.idle_add(self._update_download_progress, name, 0.0, f"Erro: {str(e)}")
            GLib.idle_add(self.show_notification, f"Erro ao instalar {name}: {str(e)}")
            GLib.idle_add(self._update_action_button, button, name, False)
            GLib.idle_add(lambda: self.downloads.pop(name, None) and self.download_threads.pop(name, None) and self.refresh_downloads_list())

    def _update_download_progress(self, app_name, fraction, status_text):
        """Atualiza o progresso de download na UI."""
        if app_name in self.downloads:
            self.downloads[app_name].update({"progress": fraction, "status": status_text, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.update_download_history(app_name, self.downloads[app_name])
            self.refresh_downloads_list()

    def _update_action_button(self, button, app_name, installed):
        """Atualiza o estado do botão de instalar/remover."""
        button.set_sensitive(True)
        button.set_label("Remover" if installed else "Instalar")
        button.get_style_context().remove_class("suggested-action")
        button.get_style_context().remove_class("destructive-action")
        button.get_style_context().add_class("destructive-action" if installed else "suggested-action")
        app = next((a for a in self.apps if a["name"] == app_name), None)
        if app:
            GLib.idle_add(self.show_app_details, app, self.store_stack, "apps")
            GLib.idle_add(self.show_app_details, app, self.my_apps_stack, "list")

    def _remove_appimage(self, name, button):
        """Remove um AppImage e sua entrada de desktop."""
        appimage_path = os.path.join(self.appimage_dir, f"{name}.AppImage")
        desktop_path = os.path.expanduser(f"~/.local/share/applications/{name}.desktop")
        icon_path = os.path.join(self.icon_dir, f"{quote(name)}.png")

        try:
            for path in [appimage_path, desktop_path, icon_path]:
                if os.path.exists(path):
                    os.remove(path)
            GLib.idle_add(self.show_notification, f"{name} removido com sucesso!")
            GLib.idle_add(self.refresh_app_list)
            GLib.idle_add(self._update_action_button, button, name, False)
        except Exception as e:
            GLib.idle_add(self.show_notification, f"Erro ao remover {name}: {e}")
            GLib.idle_add(self._update_action_button, button, name, os.path.exists(appimage_path))

    def show_notification(self, message):
        """Exibe uma notificação."""
        dialog = Gtk.MessageDialog(transient_for=self, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=message)
        dialog.run()
        dialog.destroy()

    def show_error_dialog(self, message, offer_retry):
        """Exibe um diálogo de erro com opção de tentar novamente, se aplicável."""
        dialog = Gtk.MessageDialog(transient_for=self, message_type=Gtk.MessageType.ERROR,
                                  buttons=Gtk.ButtonsType.YES_NO if offer_retry else Gtk.ButtonsType.OK, text="Erro")
        dialog.format_secondary_text(message)
        if offer_retry:
            dialog.format_secondary_text(f"{message}\n\nTentar novamente?")
        if dialog.run() == Gtk.ResponseType.YES and offer_retry:
            self.load_apps_from_url()
        dialog.destroy()

    def _create_completion_model(self):
        """Cria modelo para autocompletar busca."""
        model = Gtk.ListStore(str)
        for app in self.apps:
            model.append([app["name"]])
            model.append([app["category"]])
            for tag in app.get("tags", []):
                model.append([tag])
        return model

def main():
    app = AppImageShop()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()