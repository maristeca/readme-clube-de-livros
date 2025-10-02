**Disciplina:** Programação Web, Projeto e Desenvolvimento de Sistemas, Banco de Dados II

**Alunos:** Maria Clara Sanagioto, Maria Estela, Mariana

**Professores:** Camila Santos, Eudóxia Moura, Marcos Faino

# Descrição Geral do Sistema

O sistema **LeituraPlay** tem como objetivo permitir que usuários registrem, consultem e compartilhem indicações de livros de forma organizada e intuitiva. Ele possibilita que cada usuário cadastre um livro com título, autor e comentário/motivo da indicação, visualize todas as recomendações, participe de comunidades de leitura e avalie livros. Os administradores podem gerenciar usuários, livros e comunidades.

## Pesquisa Desk

Levantamento de requisitos realizado por meio de entrevistas com leitores, análise de aplicativos de recomendações literárias e plataformas de leitura online. Foram identificadas necessidades de fácil cadastro, organização das indicações, possibilidade de interação entre usuários e controle administrativo eficiente.

## Atores / Personas

* **Usuário Leitor:** Cadastra indicações de livros, avalia obras, participa de comunidades e consulta estatísticas.
* **Administrador:** Gerencia usuários, livros e comunidades, garantindo integridade e organização do sistema.

# Requisitos Funcionais (CASOS DE USO)

* Permitir **cadastro de usuários**.
* Permitir **autenticação e login** de usuários.
* Permitir **cadastro de livros** com título, autor e gênero.
* Permitir **indicação de livros** com comentário/motivo.
* Permitir **avaliação de livros** com nota e comentário.
* Listar todas as **indicações e avaliações** cadastradas.
* Permitir **edição e exclusão** de indicações, livros e avaliações (para usuários e admin).
* Permitir **participação em comunidades** e gerenciamento de comunidades pelo admin.
* Permitir **visualização de estatísticas** de indicações, avaliações e participação.

# Requisitos Não Funcionais

* Interface amigável, responsiva e compatível com dispositivos móveis.
* Segurança no acesso (autenticação, autorização e gerenciamento de permissões).
* Disponibilidade do sistema 24/7.
* Backup automático do banco de dados SQLite.
* Tempo de resposta inferior a 2 segundos por operação.
* Sistema leve e de fácil manutenção, desenvolvido em **Flask + Python 3.x**.

# Referências

* Livros sobre Flask, Python e Banco de Dados.
* Documentação oficial do Flask e SQLAlchemy.
* Aplicativos de leitura e recomendações literárias (como Goodreads e Skoob).
