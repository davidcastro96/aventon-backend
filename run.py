# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Asegúrate de ejecutar este archivo con 'python run.py'
    app.run(debug=True)