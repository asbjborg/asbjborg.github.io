# Personal Blog

Jekyll site using the [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) theme, deployed to GitHub Pages.

## Setup

```bash
git clone https://github.com/asbjborg/asbjborg.github.io.git
cd asbjborg.github.io
bundle install
bundle exec jekyll serve
```

Open [http://localhost:4000](http://localhost:4000)

## Writing & Publishing Posts

1. Add a file under `_posts/` named `YYYY-MM-DD-slug.md`
2. Use this frontmatter (tags only — no categories):

   ```yaml
   ---
   title: "Your Post Title"
   date: 2026-05-19 10:20:00 +0200
   last_modified_at: 2026-05-19 10:20:00 +0200
   tags: [short-stories]
   image: /assets/img/posts/your-banner.png
   ---
   ```

   `image` is optional. Banner images live in `assets/img/posts/`.

3. Commit the markdown and any new assets
4. Push to `main` — the [pages-deploy workflow](.github/workflows/pages-deploy.yml) builds and publishes automatically

Pull requests to `main` run [CI](.github/workflows/ci.yml): Jekyll build, link check, and markdownlint.

## Customization

- Site settings: `_config.yml`
- Author info: `_data/authors.yml`
- Tabs/pages: `_tabs/`
