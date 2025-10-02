from flask import Flask, render_template, request, redirect, url_for

# 1. Configuração do Flask
app = Flask(__name__)

# --- ROTAS DE PÁGINAS ESTÁTICAS (Todas as suas páginas) ---

# Rota da página inicial (base.html)
@app.route('/')
def index():
    # O Flask procura por 'base.html' na pasta 'templates/'
    return render_template('base.html')

# Rota de Login
@app.route('/login')
def login():
    return render_template('login.html')

# Rota de Cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# Rota do Feed (página após login)
@app.route('/feed')
def feed():
    # Aqui, no futuro, você pode checar se o usuário está logado
    return render_template('feed.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/comunidades')
def comunidades():
    return render_template('comunidades.html')

@app.route('/avaliar')
def avaliar():
    return render_template('avaliar.html')


# --- ROTA DE PROCESSAMENTO DE LOGIN/CADASTRO ---

# 2. Rota para receber dados do formulário de Login
@app.route('/entrar', methods=['POST'])
def processar_login():
    # Pega os dados que o formulário enviou
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    # *** LÓGICA DE VERIFICAÇÃO SIMPLES (PARA TESTE INICIAL) ***
    if email == "teste@email.com" and senha == "123":
        # Se a senha e email estiverem corretos, redireciona para o feed
        return redirect(url_for('feed'))
    else:
        # Se estiver incorreto, volta para a tela de login (você pode adicionar uma mensagem de erro aqui)
        return redirect(url_for('login'))


# 3. Rota para receber dados do formulário de Cadastro
@app.route('/cadastrar_novo', methods=['POST'])
def processar_cadastro():
    # Pega os dados que o formulário enviou
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')

    # No futuro, você salvaria isso em um banco de dados. Por enquanto, só redireciona:
    print(f"Novo usuário cadastrado: {nome}, {email}")
    
    # Redireciona para o login ou diretamente para o feed após o cadastro
    return redirect(url_for('feed'))


# Rodar o aplicativo
if __name__ == '__main__':
    # Você precisa instalar o Flask: pip install Flask
    app.run(debug=True)