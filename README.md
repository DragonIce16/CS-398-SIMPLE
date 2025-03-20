# CS-398-SIMPLE

1. Run docker-compose up -d --build
2. Run docker-compose exec app python3.7 -m pip install -e ./environments/boop
3. Run xhost + localhost
4. Run docker-compose exec app python3.7 test_gui.py -d -e boop
