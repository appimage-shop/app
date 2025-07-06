## AppImage Shop

AppImage Shop é uma aplicação desktop baseada em GTK projetada para simplificar a descoberta, instalação e gerenciamento de aplicações AppImage em sistemas Linux. Ela oferece uma interface amigável para navegar por uma lista selecionada de AppImages, baixá-los e instalá-los, e gerenciar instalações existentes, incluindo integração automática com o desktop e gerenciamento de ícones.

### Funcionalidades

  * **Navegar e Descobrir:** Explore um catálogo de aplicações AppImage obtidas de uma fonte de dados JSON remota.
  * **Filtragem por Categoria:** Filtre aplicações por categoria para uma navegação mais fácil.
  * **Funcionalidade de Pesquisa:** Encontre rapidamente aplicações usando a barra de pesquisa integrada.
  * **Detalhes da Aplicação:** Visualize informações detalhadas para cada AppImage, incluindo descrição, versão, categoria e capturas de tela.
  * **Instalação e Gerenciamento:**
      * **Instalação com um Clique:** Baixe e instale AppImages com um único clique.
      * **Acompanhamento do Progresso de Download:** Monitore o progresso dos downloads em andamento dentro da aplicação.
      * **Suporte a Cancelamento:** Cancele downloads ativos, se necessário.
      * **Integração com o Desktop:** Cria automaticamente entradas `.desktop` e gerencia ícones para AppImages instalados, garantindo que eles apareçam no seu lançador de aplicações.
      * **Detecção de Atualização:** Identifica e indica quando uma atualização está disponível para uma aplicação instalada.
      * **Remoção com um Clique:** Desinstale facilmente AppImages e suas entradas de desktop e ícones associados.
  * **Seção "Meus Aplicativos":** Visualize e gerencie todos os AppImages instalados.
  * **Ícones Personalizáveis:** Suporta ícones personalizados para aplicações, obtidos de suas respectivas URLs.
  * **Interface Minimalista:** Apresenta uma interface de usuário limpa, intuitiva e coesa com o tema.
  * **Tratamento de Erros:** Fornece mensagens de erro informativas para problemas de rede ou processamento de dados.

### Instalação

Para executar o AppImage Shop, você precisa ter Python 3 e PyGObject (bindings GTK 3) instalados em seu sistema.

#### Pré-requisitos:

  * Python 3.x
  * `python3-gi` (PyGObject)
  * `gir1.2-gtk-3.0`
  * `gir1.2-gdkpixbuf-2.0`

**1. Instalar Dependências (Debian/Ubuntu/Pop\!\_OS):**

```bash
sudo apt update
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 python3-requests # python3-requests pode ser necessário se não for implicitamente tratado
```

**2. Clonar o Repositório:**

(Assumindo que este `main.py` faz parte de um projeto maior, caso contrário, apenas baixe o `main.py`)

```bash
git clone https://github.com/appimage-shop/app.git
cd <diretório_do_repositório>
```

**3. Executar a Aplicação:**

```bash
python3 main.py
```

### Uso

Ao iniciar o AppImage Shop, você será apresentado à janela principal:

  * **Barra Lateral (Esquerda):**
      * **Categorias:** Clique em um botão de categoria para filtrar as aplicações exibidas. "Todas" mostrará todas as AppImages disponíveis.
  * **Área de Conteúdo Principal (Direita):**
      * **Barra de Pesquisa:** Digite na barra de pesquisa para encontrar aplicações por nome ou descrição.
      * **Cartões de Aplicação:** Cada cartão representa um AppImage, exibindo seu nome, versão e uma breve descrição. Ao passar o mouse sobre um cartão, detalhes adicionais podem ser mostrados.
      * **Aba "Loja":** Esta é a visualização padrão, exibindo todas as AppImages disponíveis com base em seus filtros.
      * **Aba "Meus Aplicativos":** Esta aba lista todas as AppImages atualmente instaladas via AppImage Shop. Ela também indica se uma atualização está disponível para uma aplicação instalada.
      * **Aba "Downloads":** Esta aba mostra o progresso em tempo real de quaisquer downloads de AppImage em andamento. Você pode cancelar downloads a partir desta visualização.

#### Interagindo com as Aplicações:

  * **Visualizando Detalhes:** Clique em qualquer cartão de aplicação nas abas "Loja" ou "Meus Aplicativos" para abrir sua visualização detalhada.
  * **Instalar/Remover:** Na visualização de detalhes da aplicação, um botão proeminente permitirá que você "Instalar" a aplicação (se não estiver instalada) ou "Remover" (se estiver instalada).
      * **Instalação:** Clicar em "Instalar" iniciará o processo de download e instalação. Você pode monitorar seu progresso na aba "Downloads". Uma vez instalada, a aplicação será integrada ao lançador de aplicações do seu sistema.
      * **Remoção:** Clicar em "Remover" solicitará uma confirmação e, em seguida, desinstalará o AppImage, sua entrada de desktop e seu ícone.
  * **Lançar:** Para aplicações instaladas, um botão "Lançar" aparecerá na visualização de detalhes, permitindo que você abra diretamente o AppImage.
  * **Botão Atualizar:** O botão de atualização na barra de título recarregará a lista de aplicações da fonte remota.

### Estrutura do Projeto

  * `main.py`: Contém todo o código-fonte da aplicação AppImage Shop.

### Notas Importantes:

  * **Armazenamento de AppImages:** Os AppImages são baixados e armazenados em `~/.local/bin/AppImages`.
  * **Armazenamento de Ícones:** Ícones personalizados para AppImages são baixados para `~/.local/share/icons/AppImageShop`.
  * **Entradas de Desktop:** Os arquivos de desktop (entradas `.desktop`) para AppImages instalados são criados em `~/.local/share/applications` para garantir que eles apareçam no seu lançador de aplicações.
  * **Conexão de Rede:** A aplicação requer uma conexão ativa com a internet para buscar a lista de AppImages disponíveis e para baixá-los.
  * **Permissões:** A aplicação define automaticamente as permissões de execução para os AppImages baixados.
  * **`gtk-update-icon-cache` e `update-desktop-database`:** A aplicação tenta executar esses comandos após instalar/remover ícones e arquivos de desktop para garantir que as alterações sejam refletidas em seu ambiente de desktop. Se esses comandos não forem encontrados ou falharem, os ícones/aplicativos podem não aparecer/desaparecer imediatamente.

### Contribuição

(Este é um projeto de código aberto!)

Se você gostaria de contribuir para o AppImage Shop, por favor, considere:
  * Relatar bugs.
  * Sugerir novas funcionalidades.
  * Enviar pull requests com seus AppImage.
