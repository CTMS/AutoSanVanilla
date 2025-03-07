PROMPT="%n@%m[%40<...<%~%<<]%(!.#.$) "

bindkey "^[[A" up-line-or-search
bindkey "^[[F" end-of-line
bindkey "^[[H" beginning-of-line
bindkey "^[[3~" delete-char

# Enable the builtin emacs(1) command line editor in sh(1),
# e.g. C-a -> beginning-of-line.
set -o emacs

# Uncomment this and comment the above to enable the builtin vi(1) command
# line editor in sh(1), e.g. ESC to go into visual mode.
# set -o vi


# some useful aliases
alias h='fc -l'
alias j=jobs
alias m=$PAGER
alias ll='ls -laFo'
alias l='ls -l'
alias g='egrep -i'

# Enable color output for ls, grep, etc.
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

autoload -Uz colors && colors
export LS_COLORS="di=34:ln=35:so=32:pi=33:ex=31:bd=36:cd=36:su=37"


# # be paranoid
# alias cp='cp -ip'
# alias mv='mv -i'
# alias rm='rm -i'

HISTFILE=~/.zsh-history
HISTSIZE=5000
HISTSIZE=5000
SAVEHIST=5000
setopt HIST_IGNORE_ALL_DUPS
setopt SHARE_HISTORY
setopt APPEND_HISTORY