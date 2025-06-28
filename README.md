# Personal Blog

A personal blog built with Jekyll and the Chirpy theme, hosted on GitHub Pages.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-blog.git
   cd your-blog
   ```

2. Install dependencies:
   ```bash
   bundle install
   ```

3. Run locally:
   ```bash
   bundle exec jekyll serve
   ```

4. Visit `http://localhost:4000` to see your blog

## Writing Posts

Create new posts in the `_posts` directory with the filename format:
```
YYYY-MM-DD-title-of-post.md
```

Add frontmatter to your posts:
```yaml
---
title: "Your Post Title"
date: YYYY-MM-DD HH:MM:SS +/-TTTT
categories: [category1, category2]
tags: [tag1, tag2]
---
```

## Deployment

The blog automatically deploys to GitHub Pages when you push to the `main` branch.

## Customization

- Edit `_config.yml` for site settings
- Modify `_data/` files for site data
- Customize styling in `_sass/` and `assets/css/`
- Update author information in `_data/authors.yml`
