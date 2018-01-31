#----------------------------------------------------------------------
# Initialize environment and alias
#----------------------------------------------------------------------
alias ls='ls --color'
alias ll='ls -lh'
alias la='ls -lAh'
alias grep='grep --color=tty'
alias nvim='/usr/local/opt/bin/vim --cmd "let g:vim_startup=\"nvim\""'
alias mvim='/usr/local/opt/bin/vim --cmd "let g:vim_startup=\"mvim\""'
alias tmux='tmux -2'

# default editor
export EDITOR=vim
# export TERM=xterm-256color

# disable ^s and ^q
# stty -ixon 2> /dev/null

# setup for go if it exists
if [ -d "$HOME/.local/go" ]; then
	export GOPATH="$HOME/.local/go"
	if [ -d "$HOME/.local/go/bin" ]; then
		export PATH="$HOME/.local/go/bin:$PATH"
	fi
fi

# setup for go if it exists
if [ -d /usr/local/app/go ]; then
	export GOROOT="/usr/local/app/go"
	export PATH="/usr/local/app/go/bin:$PATH"
fi

# setup for nodejs
if [ -d /usr/local/app/node ]; then
	export PATH="/usr/local/app/node/bin:$PATH"
fi

# setup for cheat
if [ -d "$HOME/.vim/vim/cheat" ]; then
	export DEFAULT_CHEAT_DIR=~/.vim/vim/cheat
fi


#----------------------------------------------------------------------
# detect vim folder
#----------------------------------------------------------------------
if [ -n "$VIM_CONFIG" ]; then
	[ ! -d "$VIM_CONFIG/etc" ] && VIM_CONFIG=""
fi

if [ -z "$VIM_CONFIG" ]; then
	if [ -d "$HOME/.vim/vim/etc" ]; then
		VIM_CONFIG="$HOME/.vim/vim"
	elif [ -d "/mnt/d/ACM/github/vim/etc" ]; then
		VIM_CONFIG="/mnt/d/ACM/github/vim"
	elif [ -d "/d/ACM/github/vim/etc" ]; then
		VIM_CONFIG="/d/ACM/github/vim/etc"
	elif [ -d "/cygdrive/d/ACM/github/vim/etc" ]; then
		VIM_CONFIG="/cygdrive/d/ACM/github/vim"
	fi
fi

[ -z "$VIM_CONFIG" ] && VIM_CONFIG="$HOME/.vim/vim"

export VIM_CONFIG

[ -d "$VIM_CONFIG/cheat" ] && export DEFAULT_CHEAT_DIR="$VIM_CONFIG/cheat"

export CHEATCOLORS=true

if [ -f "$HOME/.local/lib/python/compinit.py" ]; then
	export PYTHONSTARTUP="$HOME/.local/lib/python/compinit.py"
fi


#----------------------------------------------------------------------
# exit if not bash/zsh, or not in an interactive shell
#----------------------------------------------------------------------
[ -z "$BASH_VERSION" ] && [ -z "$ZSH_VERSION" ] && return
[[ $- != *i* ]] && return


#----------------------------------------------------------------------
# keymap
#----------------------------------------------------------------------

# default bash key binding
if [ -n "$BASH_VERSION" ]; then

	bind '"\eh":"\C-b"'
	bind '"\el":"\C-f"'
	bind '"\ej":"\C-n"'
	bind '"\ek":"\C-p"'

	bind '"\eH":"\eb"'
	bind '"\eL":"\ef"'
	bind '"\eJ":"\C-a"'
	bind '"\eK":"\C-e"'

	bind '"\e;":"ll\n"'
	bind '"\eo":"cd ..\n"'
	bind '"\eu":"ranger_cd\n"'

elif [ -n "$ZSH_VERSION" ]; then

	bindkey -s '\e;' 'll\n'
	bindkey -s '\eu' 'ranger_cd\n'

fi



#----------------------------------------------------------------------
# https://github.com/rupa/z
#----------------------------------------------------------------------
if [ -n "$BASH_VERSION" ]; then
	if [ -z "$(type -t _z)" ]; then
		[ -f "$HOME/.local/etc/z.sh" ] && . "$HOME/.local/etc/z.sh"
	fi
fi


#----------------------------------------------------------------------
# quick functions
#----------------------------------------------------------------------
gdbtool () { emacs --eval "(gdb \"gdb --annotate=3 -i=mi $*\")";}

ranger_cd () {
    tempfile="$(mktemp -t tmp.XXXXXXXX)"
    ranger --choosedir="$tempfile" "${@:-$PWD}"
	if [ -f "$tempfile" ]; then
		local new_dir=$(cat -- "$tempfile")
		rm -r -- "$tempfile"
		if [ "$new_dir" != "$PWD" ]; then
			cd -- "$new_dir"
		fi
	fi
}


#----------------------------------------------------------------------
# acd_func 1.0.5, 10-nov-2004
#----------------------------------------------------------------------

# petar marinov, http:/geocities.com/h2428, this is public domain
cd_func ()
{
  local x2 the_new_dir adir index
  local -i cnt

  if [[ $1 ==  "--" ]]; then
    dirs -v
    return 0
  fi

  the_new_dir=$1
  [[ -z $1 ]] && the_new_dir=$HOME

  if [[ ${the_new_dir:0:1} == '-' ]]; then
    #
    # Extract dir N from dirs
    index=${the_new_dir:1}
    [[ -z $index ]] && index=1
    adir=$(dirs +$index)
    [[ -z $adir ]] && return 1
    the_new_dir=$adir
  fi

  #
  # '~' has to be substituted by ${HOME}
  [[ ${the_new_dir:0:1} == '~' ]] && the_new_dir="${HOME}${the_new_dir:1}"

  #
  # Now change to the new dir and add to the top of the stack
  pushd "${the_new_dir}" > /dev/null
  [[ $? -ne 0 ]] && return 1
  the_new_dir=$(pwd)

  #
  # Trim down everything beyond 11th entry
  popd -n +11 2>/dev/null 1>/dev/null

  #
  # Remove any other occurence of this dir, skipping the top of the stack
  for ((cnt=1; cnt <= 10; cnt++)); do
    x2=$(dirs +${cnt} 2>/dev/null)
    [[ $? -ne 0 ]] && return 0
    [[ ${x2:0:1} == '~' ]] && x2="${HOME}${x2:1}"
    if [[ "${x2}" == "${the_new_dir}" ]]; then
      popd -n +$cnt 2>/dev/null 1>/dev/null
      cnt=cnt-1
    fi
  done

  return 0
}


if [ -n "$BASH_VERSION" ]; then
	alias cd=cd_func
	alias d='cd_func --'
fi


