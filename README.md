# AppImage Shop

AppImage Shop é uma aplicação desktop amigável construída com GTK3 que oferece uma vitrine selecionada para descobrir, instalar e gerenciar AppImages em seu sistema Linux. Ela visa simplificar o processo de obtenção e execução de seus aplicativos favoritos, especialmente para ambientes de desktop XFCE.

## Funcionalidades

* **Lista de Aplicativos Curada**: Navegue por uma coleção de aplicativos populares disponíveis como AppImages.
* **Categorias e Pesquisa**: Filtre facilmente aplicativos por categoria ou pesquise por aplicativos específicos por nome ou descrição.
* **Detalhes do Aplicativo**: Visualize informações detalhadas sobre cada aplicativo, incluindo sua descrição, versão e categoria.
* **Instalação/Desinstalação com Um Clique**: Instale e remova AppImages de forma contínua com um único clique.
* **Acompanhamento de Progresso**: Monitore o progresso de seus downloads ativos.
* **Integração com XFCE**: Otimizado para ambientes de desktop XFCE, fornecendo integração de menu para AppImages instalados.
* **Fonte de Dados Externa**: Os dados dos aplicativos são carregados de uma URL JSON externa, facilitando a atualização dos aplicativos disponíveis sem modificar o código da aplicação.

## Capturas de Tela

*(Atualmente, não há capturas de tela disponíveis nos dados do `app.json`. Você pode querer adicionar algumas aqui para mostrar a interface do usuário!)*

## Instalação

### Pré-requisitos

* Python 3.x
* GTK 3 (bibliotecas e arquivos de desenvolvimento)
* `python3-gi` (bindings Python para GObject Introspection)
* `xdg-utils` (para integração com o menu do desktop)
* `wget` ou `curl` (para baixar arquivos, geralmente já instalados na maioria das distros)

**Instruções de Instalação por Distribuição:**

A AppImage Shop requer algumas bibliotecas e ferramentas para funcionar corretamente. Use o gerenciador de pacotes da sua distribuição para instalá-las:

* **Em sistemas baseados em Debian/Ubuntu:**
    ```bash
    sudo apt update
    sudo apt install python3 python3-gi gir1.2-gtk-3.0 xdg-utils wget
    ```

* **Em sistemas Fedora/RHEL/CentOS:**
    ```bash
    sudo dnf install python3 python3-gobject gtk3-devel xdg-utils wget
    ```

* **Em sistemas Arch Linux:**
    ```bash
    sudo pacman -S python python-gobject gtk3 xdg-utils wget
    ```

* **Em sistemas openSUSE:**
    ```bash
    sudo zypper install python3 python3-gobject gtk3-devel xdg-utils wget
    ```

### Executando a Aplicação

1.  **Baixe o arquivo diretamente do nosso site:**
    ```bash
    Site aqui
    ```
2.  **Execute a aplicação:**
    ```bash
    python3 main.py
    ```

## Como Usar

1.  **Navegar por Aplicativos**: A janela principal exibe uma grade de aplicativos disponíveis. Você pode rolar por eles ou usar as categorias na barra lateral.
2.  **Pesquisar**: Use a barra de pesquisa na parte superior para encontrar aplicativos específicos.
3.  **Filtrar por Categoria**: Clique nas categorias na barra lateral esquerda para refinar a lista de aplicativos.
4.  **Ver Detalhes**: Clique em qualquer cartão de aplicativo para ver sua descrição detalhada, versão e outras informações.
5.  **Instalar um AppImage**: Na visualização de detalhes, clique no botão "Instalar". Uma caixa de diálogo de confirmação aparecerá. Uma vez confirmado, o download começará, e você poderá monitorar seu progresso na aba "Downloads".
    * AppImages instalados serão colocados em `~/.local/bin/AppImages/` e tornados executáveis.
    * Uma entrada `.desktop` será criada em `~/.local/share/applications/` e integrada ao menu de aplicativos do seu ambiente de desktop (otimizado para XFCE).
6.  **Remover um AppImage**: Se um aplicativo já estiver instalado, o botão na visualização de detalhes mudará para "Remover". Clique nele para desinstalar o AppImage e remover sua entrada no desktop.
7.  **Atualizar**: Clique no ícone de atualização na barra de cabeçalho para recarregar a lista de aplicativos da fonte de dados externa.

## Configuração

A aplicação carrega sua lista de AppImages disponíveis de um arquivo JSON hospedado online. Você pode alterar a URL modificando a `APPS_DATA_URL` variável em `main.py`:

```python
APPS_DATA_URL = "[https://raw.githubusercontent.com/appimage-shop/app/refs/heads/main/app.json]"
```

## Esquema dos apps via json:
    
    [
      {
          "name": "Application Name",
          "description": "A short description of the application.",
          "appimage_url": "URL_TO_APPIMAGE_FILE",
          "icon": "icon-name-from-theme",
          "category": "Software Category",
          "app": "Another Category Identifier (e.g., Graphics, Multimedia)",
          "version": "1.0.0",
          "details": "A more detailed description of the application.",
          "screenshots": []
      }
    ]
    
