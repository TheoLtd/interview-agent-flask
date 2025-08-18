from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # 在生产环境中建议禁用debug模式
    # is_production = os.environ.get('FLASK_ENV') == 'production'
    # app.run(host='0.0.0.0', port=8836, debug=not is_production)
    # app.run(host='0.0.0.0', port=8836, debug=False)
    app.run(debug=True, host='127.0.0.1', port=8836)