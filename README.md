## AppImage Shop

O **AppImage Shop** é uma aplicação desktop baseada em GTK, criada para tornar a experiência de encontrar, instalar e gerenciar AppImages no Linux muito mais fácil. Ele oferece uma interface intuitiva para navegar por um catálogo selecionado de AppImages, fazer o download, instalar e controlar as aplicações já existentes, incluindo integração automática com o ambiente de desktop e gerenciamento de ícones.

### Principais Funcionalidades

  * **Navegar e Descobrir:** Explore um vasto catálogo de aplicações AppImage, obtido de uma fonte de dados JSON remota.
  * **Navegação Inteligente:** Filtre os aplicativos por categoria e use a barra de pesquisa integrada para encontrar rapidamente o que você precisa.
  * **Informações Detalhadas:** Visualize informações completas sobre cada AppImage, como descrição, versão, categoria e capturas de tela.
  * **Instalação e Gerenciamento Descomplicado:**
      * **Instalação com Um Clique:** Baixe e instale AppImages de forma simples e rápida.
      * **Monitoramento de Download:** Acompanhe o progresso dos downloads em tempo real e cancele-os se precisar.
      * **Integração Perfeita com o Desktop:** Automaticamente cria entradas `.desktop` e gerencia ícones, garantindo que seus AppImages apareçam no lançador de aplicações.
      * **Detecção de Atualizações:** O sistema avisa quando há uma nova versão disponível para uma aplicação instalada.
      * **Remoção Instantânea:** Desinstale AppImages, suas entradas de desktop e ícones associados com um único clique.
  * **Seção "Meus Aplicativos":** Uma área dedicada para visualizar e gerenciar todos os AppImages instalados via AppImage Shop.
  * **Ícones Personalizáveis:** Suporte para ícones personalizados, obtidos diretamente das URLs das aplicações.
  * **Interface Minimalista:** Uma experiência de usuário limpa, intuitiva e que se alinha perfeitamente com o tema do seu sistema.
  * **Tratamento de Erros Eficaz:** Mensagens de erro claras e informativas para problemas de rede ou processamento de dados.

### Instalação

Para usar o AppImage Shop, você precisará do **Python 3** e do **PyGObject (bindings GTK 3)** em seu sistema.

#### Pré-requisitos

  * Python 3.x
  * `python3-gi` (PyGObject)
  * `gir1.2-gtk-3.0`
  * `gir1.2-gdkpixbuf-2.0`
  * `python3-requests` (pode ser necessário)

#### Passos para Instalação

1.  **Instalar Dependências (Debian/Ubuntu/Pop\!\_OS):**
    ```bash
    sudo apt update
    sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 python3-requests
    ```
2.  **Clonar o Repositório:**
    ```bash
    git clone https://github.com/appimage-shop/app.git
    cd <diretorio_do_repositorio>
    ```
3.  **Executar o Instalador:**
    ```bash
    python3 installer.py
    ```

### Uso

Ao iniciar o AppImage Shop, você verá a janela principal, organizada em seções:

  * **Barra Lateral (Esquerda):**
      * **Categorias:** Clique em um botão de categoria para filtrar os aplicativos exibidos. A opção "Todas" mostra todos os AppImages disponíveis.
  * **Área de Conteúdo Principal (Direita):**
      * **Barra de Pesquisa:** Digite para encontrar aplicativos por nome ou descrição.
      * **Cartões de Aplicação:** Cada cartão representa um AppImage, mostrando seu nome, versão e uma breve descrição.
      * **Aba "Loja":** A visualização padrão, com todos os AppImages disponíveis de acordo com seus filtros.
      * **Aba "Meus Aplicativos":** Lista todos os AppImages instalados via AppImage Shop, indicando se há atualizações disponíveis.
      * **Aba "Downloads":** Mostra o progresso em tempo real dos downloads de AppImage em andamento, com opções para cancelar.

#### Interagindo com as Aplicações

  * **Visualizando Detalhes:** Clique em qualquer cartão de aplicação para abrir a visualização detalhada.
  * **Instalar/Remover:** Na visualização detalhada, um botão proeminente permitirá que você "Instalar" (se não estiver instalado) ou "Remover" (se já estiver).
      * **Instalação:** Inicia o download e a instalação. Você pode monitorar o progresso na aba "Downloads". Após a instalação, a aplicação será integrada ao lançador do sistema.
      * **Remoção:** Solicita uma confirmação e desinstala o AppImage, sua entrada de desktop e ícone.
  * **Lançar:** Para aplicações instaladas, um botão "Lançar" aparecerá na visualização detalhada, permitindo que você abra o AppImage diretamente.
  * **Botão Atualizar:** O botão de atualização na barra de título recarrega a lista de aplicações da fonte remota.

-----

## Acesso ao Catálogo de Aplicativos AppImage (Versão de Testes)
Para que o AppImage Shop utilize este catálogo de testes em vez do catálogo padrão, você pode alterar a URL da fonte de dados nas configurações do aplicativo.

1.  Abra o **AppImage Shop**.
2.  Navegue até o **menu de configurações**.
3.  Selecione a aba Downloads.
4.  Procure pela opção "URL do json de aplicativos".
5.  Altere o valor para:
    ```
    https://raw.githubusercontent.com/appimage-shop/testing/refs/heads/main/app.json
    ```
6.  Salve as alterações e atualize a AppImage Shop para que o novo catálogo seja carregado.

-----

## Contribuição

Ambos os projetos são de código aberto\! Se você quiser contribuir para o AppImage Shop, considere:

  * Relatar **bugs**.
  * Sugerir novas **funcionalidades**.
  * Enviar **pull requests** com seus AppImages.

-----

Com essas ferramentas, gerenciar AppImages no Linux se torna uma tarefa muito mais simples e eficiente!
