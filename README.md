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

## Editor App.json

O **App.json Editor** é um editor gráfico de arquivos JSON, que atua como uma ferramenta complementar ao AppImage Shop. Sua função principal é gerenciar a lista de aplicativos que o AppImage Shop exibe, permitindo que os mantenedores adicionem, editem ou removam entradas sem precisar editar o JSON manualmente.

### Funcionalidades do Editor

  * **Carregar e Salvar Arquivos JSON:** Carregue arquivos `app.json` (ou outros JSONs) e salve as alterações.
  * **Interface Gráfica (GTK):** Desenvolvido com GTK 3 para uma experiência visual amigável.
  * **Visualização em Lista:** Exibe os aplicativos em uma TreeView com colunas para "Nome", "Versão" e "Categoria".
  * **Gerenciamento de Aplicativos:**
      * **Adicionar Novos:** Inclua novas entradas de aplicativos no arquivo JSON.
      * **Editar Existentes:** Edite detalhes como Nome, Descrição, URLs (AppImage, Ícone), Categoria (em português e inglês), Versão, Detalhes e Capturas de Tela (separadas por vírgula).
      * **Excluir:** Remova aplicativos selecionados da lista.
  * **Notificações ao Usuário:** Mensagens claras de sucesso ou erro para todas as operações.
  * **Seleção de Arquivo:** Inclui um seletor para abrir diferentes arquivos JSON.
  * **Seção "Sobre":** Fornece informações sobre o desenvolvedor e o propósito do editor.

### Como o Editor se Relaciona com o AppImage Shop

O `editor.py` é essencial para manter o catálogo do AppImage Shop atualizado. Ele capacita os mantenedores a gerenciar os dados dos aplicativos, garantindo que o AppImage Shop sempre ofereça uma lista precisa e relevante de softwares.

### Utilização do Editor

Para executar o editor, você precisará das mesmas dependências Python e GTK do AppImage Shop.

```bash
python3 editor.py
```

-----

## Contribuição

Ambos os projetos são de código aberto\! Se você quiser contribuir para o AppImage Shop, considere:

  * Relatar **bugs**.
  * Sugerir novas **funcionalidades**.
  * Enviar **pull requests** com seus AppImages.

-----

Com essas ferramentas, gerenciar AppImages no Linux se torna uma tarefa muito mais simples e eficiente\!
