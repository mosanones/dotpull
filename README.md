# dotpull

> Sync and version your dotfiles across machines with profile-based overrides.

---

## Installation

```bash
pip install dotpull
```

Or install from source:

```bash
git clone https://github.com/yourusername/dotpull.git && cd dotpull && pip install .
```

---

## Usage

Initialize a new dotpull repository and push your dotfiles:

```bash
dotpull init
dotpull add ~/.bashrc ~/.vimrc ~/.gitconfig
dotpull push
```

Pull dotfiles on another machine:

```bash
dotpull pull
```

Use profiles to apply machine-specific overrides:

```bash
dotpull profile create work
dotpull add ~/.bashrc --profile work
dotpull apply --profile work
```

List tracked files and active profile:

```bash
dotpull status
```

---

## Configuration

dotpull stores its configuration in `~/.dotpull/config.toml`. Profiles are defined as named sections and can override any tracked file on a per-machine basis.

---

## License

This project is licensed under the [MIT License](LICENSE).