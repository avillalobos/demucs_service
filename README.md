# demucs_service

Creating the download DB:

    create table downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, song_path TEXT, download_url TEXT, accessed BOOLEAN);