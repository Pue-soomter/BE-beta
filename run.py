from app import app,api

if __name__ == "__main__":
    from resources import create_api, create_api_models

    create_api_models(api)
    create_api(api)

    print("Now we Run...")
    # api.run()
    app.run(debug=False)
