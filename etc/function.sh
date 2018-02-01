# returns for non-interactive shells
[[ $- != *i* ]] && return


#----------------------------------------------------------------------
# quick functions
#----------------------------------------------------------------------
gdbtool () { emacs --eval "(gdb \"gdb --annotate=3 -i=mi $*\")";}

ranger_cd () {
    tempfile="$(mktemp -t tmp.XXXXXXXX)"
    ranger --choosedir="$tempfile" "${@:-$PWD}"
	if [ -n "$tempfile" ] && [ -f "$tempfile" ]; then
		local new_dir=$(cat -- "$tempfile")
		rm -f -- "$tempfile"
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


#----------------------------------------------------------------------
# change title
#----------------------------------------------------------------------
settitle () 
{ 
  echo -ne "\e]2;$@\a\e]1;$@\a"; 
}


#----------------------------------------------------------------------
# zsh skwp theme
#----------------------------------------------------------------------
if [ -n "$ZSH_VERSION" ]; then
	function _prompt_skwp_init {
		# Use extended color pallete if available.
		if [[ $TERM = *256color* || $TERM = *rxvt* ]]; then
			_prompt_skwp_colors=(
			"%F{81}"  # Turquoise
			"%F{166}" # Orange
			"%F{135}" # Purple
			"%F{161}" # Hotpink
			"%F{118}" # Limegreen
			"%F{1}"   # Darkred
			)
		else
			_prompt_skwp_colors=(
			"%F{cyan}"
			"%F{yellow}"
			"%F{magenta}"
			"%F{red}"
			"%F{green}"
			"%F{1}"   # Darkred
			)
		fi

		local reset_color="%F{7}"
		PROMPT="${_prompt_skwp_colors[3]}%n%f@${_prompt_skwp_colors[2]}%m%f ${_prompt_skwp_colors[5]}%~%f %{$reset_color%}$ "
		RPROMPT="%{$_prompt_skwp_colors[6]%}%(?..%?)%{$reset_color%}"
	}
fi


#----------------------------------------------------------------------
# advance keymap
#----------------------------------------------------------------------

# default bash key binding
if [ -n "$BASH_VERSION" ]; then
	bind '"\eu":"ranger_cd\n"'
	bind '"\eOS":"vim "'
	bind '"\e[15~":"\$(__fzf_cd__)\n"'
elif [ -n "$ZSH_VERSION" ]; then
	bindkey -s '\eOS' 'vim '
	bindkey -s '\eu' 'ranger_cd\n'
	bindkey '\e[15~' fzf-cd-widget
fi



