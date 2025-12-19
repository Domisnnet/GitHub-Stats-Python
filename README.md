# 📊 Gerador de Estatísticas do GitHub

![Status do Deploy](https://img.shields.io/badge/Status-Online-brightgreen)
![Tecnologias](https://img.shields.io/badge/Tecnologias-HTML%20%7C%20CSS%20%7C%20JS%20%7C%20Python-blue)
[![Licença MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Exemplo de Dashboard](https://us-central1-github-stats-68157678-42e04.cloudfunctions.net/statsSvg?username=google&theme=tokyonight)

Crie e exiba um dashboard dinâmico com suas estatísticas do GitHub!

## 🔗 Acesse a Aplicação!

Clique no link abaixo para gerar seu dashboard agora mesmo:

**[https://github-stats-68157678-42e04.web.app/](https://github-stats-68157678-42e04.web.app/)**

---

## Sobre a Aplicação 🚀

O **Gerador de Estatísticas do GitHub** é uma aplicação web que cria uma imagem SVG com as estatísticas de um desenvolvedor, como número de repositórios, estrelas e forks. A aplicação consome os dados diretamente da API do GitHub e os renderiza em um card customizável.

## Como Usar 🎮

1.  **Acesse o Site:** Use o link acima para abrir a aplicação.
2.  **Informe o Usuário:** Digite o nome de usuário do GitHub que você deseja consultar.
3.  **Escolha um Tema:** Selecione um dos temas visuais disponíveis para customizar a aparência do seu card.
4.  **Gerar:** Clique em "Gerar Estatísticas" para que a mágica aconteça! O seu card de estatísticas aparecerá na tela.
5.  **Use em seu Perfil:** Você pode usar a URL da imagem gerada para exibi-la em qualquer lugar, inclusive no seu próprio `README.md` do GitHub!

## Tecnologias Utilizadas ⚙️

Este projeto foi desenvolvido com uma arquitetura moderna e desacoplada:

*   **Frontend**:
    *   **HTML5** 🌐: Estrutura semântica da página.
    *   **CSS3** 🎨: Estilização e temas visuais.
    *   **JavaScript** 💻: Lógica do cliente e manipulação do DOM.
*   **Backend**:
    *   **Python** 🐍: Linguagem usada para a lógica de backend.
    *   **Google Cloud Functions** ☁️: Plataforma serverless para executar o código que gera o SVG.
*   **Hosting**:
    *   **Firebase Hosting** 🔥: Para hospedar o site estático (frontend).

## 🤝 Como Contribuir

Sinta-se à vontade para sugerir melhorias ou reportar *bugs*. Siga estes passos para contribuir:

1.  **Faça um Fork** do projeto.
2.  **Crie uma nova Branch** (`git checkout -b feature/sua-melhoria`).
3.  **Faça o Commit** de suas alterações (`git commit -m 'Adiciona nova funcionalidade'`).
4.  **Faça o Push** para a Branch (`git push origin feature/sua-melhoria`).
5.  **Abra um Pull Request**.

## FAQ 🤔

**Pergunta 1:** Como posso usar a imagem no meu perfil do GitHub?
**Resposta:** Simples! Use o seguinte formato de URL em um arquivo Markdown:
`![Estatísticas](https://us-central1-github-stats-68157678-42e04.cloudfunctions.net/statsSvg?username=SEU-USUARIO)`
Substitua `SEU-USUARIO` pelo seu nome de usuário do GitHub.

**Pergunta 2:** As estatísticas são atualizadas?
**Resposta:** Sim! A imagem é gerada dinamicamente a cada vez que é carregada, garantindo que os dados estejam sempre atualizados com seu perfil no GitHub.

**Pergunta 3:** De onde vêm os dados?
**Resposta:** Todos os dados são obtidos em tempo real através da API pública do GitHub.

## 📄 Licença

Este projeto é *open source* e está licenciado sob a **Licença MIT**.

