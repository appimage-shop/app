import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import os
import threading
import urllib.request
import subprocess
import configparser
from urllib.parse import quote
from datetime import datetime

# URLs do main.py e do ícone no GitHub
MAIN_PY_URL = "https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/main.py"
ICON_URL = "https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/icon.png"

class AppImageShopInstaller(Gtk.Window):
    """Janela principal do instalador do AppImage Shop."""
    def __init__(self):
        super().__init__(title="Instalador do AppImage Shop")
        self.set_default_size(500, 300)
        self.set_border_width(20)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Diretórios para configuração, instalação e ícones
        self.config_dir = os.path.expanduser("~/.local/share/AppImageShop")
        self.config_file = os.path.join(self.config_dir, "config.ini")
        self.install_dir = self.config_dir
        self.icon_dir = os.path.join(self.config_dir, "icons")
        os.makedirs(self.install_dir, exist_ok=True)
        os.makedirs(self.icon_dir, exist_ok=True)

        # Inicializa configuração
        self.config = configparser.ConfigParser()
        self.load_config()

        # Aplica CSS e configura UI
        self._apply_css()
        self._setup_ui()

    def load_config(self):
        """Carrega configuração do config.ini com valores padrão."""
        defaults = {
            'Settings': {'auto_refresh': 'True', 'last_tab': '0', 'last_category': 'Todos'},
            'Accessibility': {'high_contrast': 'False', 'font_scale': '1.0'},
            'Appearance': {'theme': 'Sistema'},
            'Downloads': {'appimage_dir': os.path.expanduser("~/.local/bin/AppImages")}
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
        button {{ padding: 12px 24px; border-radius: 10px; font-weight: bold; border: {'2px solid #FFFFFF' if high_contrast else '1px solid @borders'}; }}
        button.suggested-action {{ background-color: {c['sel_bg']}; color: {c['sel_fg']}; }}
        button.suggested-action:hover {{ background-color: {'#CCCCCC' if high_contrast else f"shade({c['sel_bg']}, 0.9)"}; }}
        button.destructive-action {{ background-color: {'#FF0000' if high_contrast else '@error_bg_color'}; color: {'#FFFFFF' if high_contrast else '@error_fg_color'}; }}
        button.destructive-action:hover {{ background-color: {'#CC0000' if high_contrast else 'shade(@error_bg_color, 0.9)'}; }}
        progressbar {{ min-height: 35px; border-radius: 8px; margin: 20px; }}
        progressbar trough {{ background-color: {'#333333' if high_contrast else f"alpha({c['fg']}, 0.2)"}; }}
        progressbar progress {{ background-color: {c['sel_bg']}; }}
        label.title {{ font-size: {1.4 * font_scale}em; font-weight: bold; margin-bottom: 20px; }}
        label.status {{ font-size: {1.1 * font_scale}em; margin-top: 10px; }}
        .icon-image {{ margin-right: 10px; }}
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _setup_ui(self):
        """Configura o layout principal e widgets da UI."""
        # Barra de Cabeçalho
        header_bar = Gtk.HeaderBar(title="Instalador do AppImage Shop")
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)

        # Área Principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.add(main_box)

        # Linha do Título com Ícone
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER)
        main_box.pack_start(title_box, False, False, 0)

        # Ícone
        self.icon_image = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
        self.icon_image.get_style_context().add_class("icon-image")
        title_box.pack_start(self.icon_image, False, False, 0)
        self._load_icon_async()

        # Título
        title_label = Gtk.Label(label="Bem-vindo ao Instalador do AppImage Shop", use_markup=True)
        title_label.get_style_context().add_class("title")
        title_box.pack_start(title_label, False, False, 0)

        # Caixa de Botões
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER)
        main_box.pack_start(button_box, False, False, 0)

        # Botão de Instalação
        self.install_button = Gtk.Button(label="Iniciar Instalação")
        self.install_button.get_style_context().add_class("suggested-action")
        self.install_button.set_tooltip_text("Iniciar a instalação do AppImage Shop")
        self.install_button.connect("clicked", self.on_install_clicked)
        button_box.pack_start(self.install_button, False, False, 0)

        # Botão de Atualizar
        self.update_button = Gtk.Button(label="Atualizar")
        self.update_button.get_style_context().add_class("suggested-action")
        self.update_button.set_tooltip_text("Atualizar o AppImage Shop para a versão mais recente")
        self.update_button.connect("clicked", self.on_update_clicked)
        button_box.pack_start(self.update_button, False, False, 0)

        # Botão de Remover
        self.remove_button = Gtk.Button(label="Remover")
        self.remove_button.get_style_context().add_class("destructive-action")
        self.remove_button.set_tooltip_text("Remover o AppImage Shop do sistema")
        self.remove_button.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(self.remove_button, False, False, 0)

        # Barra de Progresso
        self.progress_bar = Gtk.ProgressBar(show_text=True, text="Aguardando início...")
        main_box.pack_start(self.progress_bar, False, False, 0)

        # Rótulo de Status
        self.status_label = Gtk.Label(label="")
        self.status_label.get_style_context().add_class("status")
        main_box.pack_start(self.status_label, False, False, 0)

    def _load_icon_async(self):
        """Carrega o ícone assincronamente para a interface."""
        icon_path = os.path.join(self.icon_dir, "icon.png")
        if os.path.exists(icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 64, 64)
                GLib.idle_add(self.icon_image.set_from_pixbuf, pixbuf)
            except Exception as e:
                print(f"Erro ao carregar ícone: {e}")
            return

        def download_icon():
            try:
                urllib.request.urlretrieve(ICON_URL, icon_path)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 64, 64)
                GLib.idle_add(self.icon_image.set_from_pixbuf, pixbuf)
            except Exception as e:
                print(f"Erro ao baixar ícone: {e}")

        threading.Thread(target=download_icon, daemon=True).start()

    def on_install_clicked(self, button):
        """Manipula o clique no botão de instalação."""
        self.install_button.set_sensitive(False)
        self.update_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.status_label.set_text("Iniciando instalação...")
        threading.Thread(target=self._install_app, daemon=True).start()

    def on_update_clicked(self, button):
        """Manipula o clique no botão de atualizar."""
        main_py_path = os.path.join(self.install_dir, "main.py")
        if not os.path.exists(main_py_path):
            self.show_notification("O AppImage Shop não está instalado. Use o botão 'Iniciar Instalação'.")
            return
        dialog = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Deseja atualizar o AppImage Shop?"
        )
        if dialog.run() == Gtk.ResponseType.YES:
            self.install_button.set_sensitive(False)
            self.update_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
            self.progress_bar.set_fraction(0.0)
            self.status_label.set_text("Iniciando atualização...")
            threading.Thread(target=self._update_app, daemon=True).start()
        dialog.destroy()

    def on_remove_clicked(self, button):
        """Manipula o clique no botão de remover."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Deseja remover o AppImage Shop?",
            secondary_text="Isso excluirá o aplicativo, sua entrada no menu e o ícone, mas manterá os arquivos de configuração."
        )
        if dialog.run() == Gtk.ResponseType.YES:
            self.install_button.set_sensitive(False)
            self.update_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
            self.progress_bar.set_fraction(0.0)
            self.status_label.set_text("Removendo AppImage Shop...")
            threading.Thread(target=self._remove_app, daemon=True).start()
        dialog.destroy()

    def _install_app(self):
        """Executa o processo de instalação."""
        try:
            # Passo 1: Instalar dependências
            GLib.idle_add(self.progress_bar.set_fraction, 0.1)
            GLib.idle_add(self.status_label.set_text, "Verificando dependências...")
            self._install_dependencies()

            # Passo 2: Baixar main.py
            GLib.idle_add(self.progress_bar.set_fraction, 0.4)
            GLib.idle_add(self.status_label.set_text, "Baixando arquivo principal...")
            main_py_path = os.path.join(self.install_dir, "main.py")
            urllib.request.urlretrieve(MAIN_PY_URL, main_py_path)
            os.chmod(main_py_path, 0o755)  # Torna executável

            # Passo 3: Baixar ícone
            GLib.idle_add(self.progress_bar.set_fraction, 0.6)
            GLib.idle_add(self.status_label.set_text, "Baixando ícone...")
            icon_path = os.path.join(self.icon_dir, "icon.png")
            urllib.request.urlretrieve(ICON_URL, icon_path)
            self._load_icon_async()  # Atualiza o ícone na interface

            # Passo 4: Criar arquivo .desktop
            GLib.idle_add(self.progress_bar.set_fraction, 0.8)
            GLib.idle_add(self.status_label.set_text, "Configurando atalho...")
            self._create_desktop_file(main_py_path)

            # Passo 5: Concluir
            GLib.idle_add(self.progress_bar.set_fraction, 1.0)
            GLib.idle_add(self.status_label.set_text, "Instalação concluída com sucesso!")
            GLib.idle_add(self.show_notification, "AppImage Shop instalado com sucesso! Você pode iniciá-lo a partir do menu de aplicativos.")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)
        except Exception as e:
            GLib.idle_add(self.progress_bar.set_fraction, 0.0)
            GLib.idle_add(self.status_label.set_text, f"Erro: {str(e)}")
            GLib.idle_add(self.show_notification, f"Erro ao instalar o AppImage Shop: {str(e)}")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)

    def _update_app(self):
        """Atualiza o AppImage Shop baixando a versão mais recente do main.py e ícone."""
        try:
            # Passo 1: Baixar main.py
            GLib.idle_add(self.progress_bar.set_fraction, 0.4)
            GLib.idle_add(self.status_label.set_text, "Baixando arquivo principal...")
            main_py_path = os.path.join(self.install_dir, "main.py")
            urllib.request.urlretrieve(MAIN_PY_URL, main_py_path)
            os.chmod(main_py_path, 0o755)  # Torna executável

            # Passo 2: Baixar ícone
            GLib.idle_add(self.progress_bar.set_fraction, 0.7)
            GLib.idle_add(self.status_label.set_text, "Baixando ícone...")
            icon_path = os.path.join(self.icon_dir, "icon.png")
            urllib.request.urlretrieve(ICON_URL, icon_path)
            self._load_icon_async()  # Atualiza o ícone na interface

            # Passo 3: Concluir
            GLib.idle_add(self.progress_bar.set_fraction, 1.0)
            GLib.idle_add(self.status_label.set_text, "Atualização concluída com sucesso!")
            GLib.idle_add(self.show_notification, "AppImage Shop atualizado com sucesso!")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)
        except Exception as e:
            GLib.idle_add(self.progress_bar.set_fraction, 0.0)
            GLib.idle_add(self.status_label.set_text, f"Erro: {str(e)}")
            GLib.idle_add(self.show_notification, f"Erro ao atualizar o AppImage Shop: {str(e)}")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)

    def _remove_app(self):
        """Remove o AppImage Shop, sua entrada no menu e o ícone."""
        try:
            main_py_path = os.path.join(self.install_dir, "main.py")
            desktop_path = os.path.expanduser("~/.local/share/applications/AppImageShop.desktop")
            icon_path = os.path.join(self.icon_dir, "icon.png")

            # Passo 1: Remover arquivos
            GLib.idle_add(self.progress_bar.set_fraction, 0.5)
            GLib.idle_add(self.status_label.set_text, "Removendo arquivos...")
            for path in [main_py_path, desktop_path, icon_path]:
                if os.path.exists(path):
                    os.remove(path)

            # Passo 2: Tentar remover diretório de ícones (se vazio)
            try:
                os.rmdir(self.icon_dir)
            except OSError:
                pass  # Diretório não está vazio

            # Passo 3: Tentar remover diretório principal (se vazio)
            try:
                os.rmdir(self.install_dir)
            except OSError:
                pass  # Diretório não está vazio (ex.: config.ini presente)

            # Passo 4: Concluir
            GLib.idle_add(self.progress_bar.set_fraction, 1.0)
            GLib.idle_add(self.status_label.set_text, "Remoção concluída com sucesso!")
            GLib.idle_add(self.show_notification, "AppImage Shop removido com sucesso!")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)
            GLib.idle_add(self.icon_image.set_from_icon_name, "application-x-executable", Gtk.IconSize.DIALOG)
        except Exception as e:
            GLib.idle_add(self.progress_bar.set_fraction, 0.0)
            GLib.idle_add(self.status_label.set_text, f"Erro: {str(e)}")
            GLib.idle_add(self.show_notification, f"Erro ao remover o AppImage Shop: {str(e)}")
            GLib.idle_add(self.install_button.set_sensitive, True)
            GLib.idle_add(self.update_button.set_sensitive, True)
            GLib.idle_add(self.remove_button.set_sensitive, True)

    def _install_dependencies(self):
        """Instala dependências necessárias (python3-gi)."""
        try:
            # Verifica se python3-gi está instalado
            subprocess.check_call(["python3", "-c", "import gi"])
        except subprocess.CalledProcessError:
            try:
                # Tenta instalar com apt (Ubuntu/Debian)
                subprocess.check_call(["sudo", "apt", "install", "-y", "python3-gi"])
            except subprocess.CalledProcessError:
                GLib.idle_add(self.show_notification, "Por favor, instale o pacote 'python3-gi' manualmente usando o gerenciador de pacotes da sua distribuição.")

    def _create_desktop_file(self, main_py_path):
        """Cria um arquivo .desktop para o AppImage Shop."""
        icon_path = os.path.join(self.icon_dir, "icon.png")
        desktop_file_content = f"""[Desktop Entry]
Name=AppImage Shop
Exec=python3 {main_py_path} %U
Type=Application
Icon={icon_path}
Terminal=false
Categories=Utility;
Comment=Loja de aplicativos AppImage
"""
        desktop_path = os.path.expanduser("~/.local/share/applications/AppImageShop.desktop")
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        with open(desktop_path, 'w') as f:
            f.write(desktop_file_content)
        os.chmod(desktop_path, 0o644)

    def show_notification(self, message):
        """Exibe uma notificação."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.INFO if "sucesso" in message.lower() else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

def main():
    win = AppImageShopInstaller()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
