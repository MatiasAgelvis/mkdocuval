# Valmore Agelvis' Website Repository

Welcome to the repository for Valmore Agelvis' personal website! This repository contains the source code for Valmore's website, which includes a blog, his CV, and a vast collection of index cards. The website showcases Valmore's work, interests, and accomplishments in various fields.

## Features

- Blog: A dedicated section where Valmore shares his thoughts, insights, and experiences with the world.
- CV: Valmore's professional resume, highlighting his education, work history, and skills.
- Index Cards: A vast collection of index cards containing valuable information on various topics.

One of the most outstanding features of this website is the automation of the generation of index cards. The process involves converting documents from odt to Word format and then converting them to Markdown using Pandoc. A regex is used to determine the foundries of each index card to set up seamless navigation.

## Tech Stack

The website is built using the following technologies:

- Python: The core language used for scripting and automation.
- Material for MkDocs: A clean and simple Material Design theme for MkDocs, providing an elegant look to the website.

The articles are hosted in this github repo and [Box](https://app.box.com/s/7s15qgb64wr6bpqhng7cgdunkzqlk9e3)

## Getting Started

### Installation

Before you start working on the website locally, ensure you have the necessary dependencies installed:

```
sudo apt install -y pandoc
pip install -r requirements.txt
```

### Update Site Content

To update the website's content, use the following command:

```
bash odt_to_html.sh
```

This script automates the conversion of odt files to HTML format, which is then used to generate the index cards in Markdown.

### Deployment

To deploy the website to GitHub Pages, use the following command:

```
mkdocs gh-deploy --force
```

This command will build the site and publish it to the `gh-pages` branch of the repository, making it publicly accessible.

### Docker Development

To build and run the website using Docker, follow these commands:

```bash
# Build the Docker image
docker build -t mkdocuval:latest .

# Run the container with local file sync
docker run --name mkdocs-container -v $(pwd):/app -p 8000:8000 mkdocuval:latest

# Stop the container
docker stop mkdocs-container

# Start an existing container
docker start mkdocs-container

# Remove the container
docker rm mkdocs-container

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a
```

The website will be available at `http://localhost:8000`. Any changes made to local files will be reflected immediately in the container due to volume mounting (`-v` flag).

### Local Development

To serve the website locally for development and testing purposes, use the following command:

```
mkdocs serve
```

This command starts a development server, allowing you to preview changes and updates to the website in real-time.

## Contributing

Contributions to Valmore Agelvis' website are welcome! If you have any suggestions, improvements, or bug fixes, please feel free to submit a pull request. We value your input and aim to create an informative and engaging platform for Valmore's work and interests.

## License

This project is licensed under the [GNU AFFERO GENERAL PUBLIC LICENSE](LICENSE). You are free to use and modify the code according to the terms specified in the license.

---

Thank you for visiting the Valmore Agelvis' Website Repository! We hope you find the content informative and enjoyable. For any queries or feedback, feel free to reach out to us at [contact](https://matiasagelvis.com/contact). Happy browsing!