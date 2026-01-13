
# Reservation autocomplete function
_slurm_cli_initialize_autocomplete() {

    # Check for optional CLI options and print their values for debugging
    local -A opts=()
    local i=1

    while [[ $i -lt ${COMP_CWORD} ]]; do
        arg="${COMP_WORDS[$i]}"
        case "$arg" in
        --version)
            opts[version]="1"
            ;;
        -h|--help)
            opts[help]="1"
            ;;
        --style)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[style]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            else
                COMPREPLY=($(compgen -W "pretty json csv" -- "$cur"))
                return
            fi
            ;;
        --pretty|-p)
            opts[pretty]="1"
            ;;
        --json|-j)
            opts[json]="1"
            ;;
        --csv)
            opts[csv]="1"
            ;;
        --delimiter|-d)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[delimiter]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            fi
            ;;
        --zebra|-z)
            opts[zebra]="1"
            ;;
        --force-update|-f)
            opts[force_update]="1"
            ;;
        --yes|-y)
            opts[yes]="1"
            ;;
        --dry-run)
            opts[dry_run]="1"
            ;;
        --no-dry-run)
            opts[no_dry_run]="1"
            ;;
        --profile|-P)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[profile]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            fi
            ;;
        --profile-str|--format|-o)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[profile_str]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            fi
            ;;
        --list-fields)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[list_fields]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            fi
            ;;
        *)
            break
            ;;
        esac
        ((i++))
    done

    if [[ ${COMP_WORDS[COMP_CWORD]:0:1} == "-" ]]; then
        COMPREPLY=($(compgen -W "-h -p -j -d -z -f -y -t -P -o --version --help --style --pretty --json --csv --delimiter --zebra --force-update --yes --dry-run --no-dry-run --cache-timeout --profile --profile-str --format --list-fields" -- "$cur"))
        return
    fi

    # Get command and resource name if any
    local cmd=""
    local resource=""
    cmd="${COMP_WORDS[$i]}"

    # Find resource by skipping over any options (words starting with -)
    local j=$((i+1))
    while [[ $j -lt ${#COMP_WORDS[@]} ]]; do
        local word="${COMP_WORDS[$j]}"
        if [[ "$word" != -* ]]; then
            resource="$word"
            break
        fi
        # Skip option value if this option takes an argument
        case "$word" in
            --style|--delimiter|-d|-t|--cache-timeout)
                ((j++))
                ;;
        esac
        ((j++))
    done
    # echo -e "\nCOMP_CWORD=$COMP_CWORD; i=$i j=$j \
    # COMP_WORDS=${COMP_WORDS[@]} \
    # Current=${COMP_WORDS[COMP_CWORD]} cmd=$cmd resource=$resource"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Guess the command by prefix - generated from COMMANDS config
    local guessed="no"
    case "$cmd" in
        sh*|g*)
            guessed="show"
            cmd="show"
            ;;
        cr*|n*|ad*)
            guessed="create"
            cmd="create"
            ;;
        up*|e*|ch*|m*|se*)
            guessed="update"
            cmd="update"
            ;;
        de*|rem*|rm)
            guessed="delete"
            cmd="delete"
            ;;
        list-*|ls|list)
            guessed="list-resources"
            cmd="list-resources"
            ;;
        au*)
            guessed="autocomplete"
            cmd="autocomplete"
            ;;
        he*)
            guessed="help"
            cmd="help"
            ;;
        v*)
            guessed="version"
            cmd="version"
            ;;
        rec*|co*)
            guessed="reconfigure"
            cmd="reconfigure"
            ;;
        p*)
            guessed="ping"
            cmd="ping"
            ;;
        ta*)
            guessed="takeover"
            cmd="takeover"
            ;;
        tok*)
            guessed="token"
            cmd="token"
            ;;
        dr*)
            guessed="drain"
            cmd="drain"
            ;;
        un*|res*)
            guessed="undrain"
            cmd="undrain"
            ;;
        reb*)
            guessed="reboot"
            cmd="reboot"
            ;;
        ca*)
            guessed="cancel_reboot"
            cmd="cancel_reboot"
            ;;
        ho*)
            guessed="hold"
            cmd="hold"
            ;;
        rel*)
            guessed="release"
            cmd="release"
            ;;
        top)
            guessed="top"
            cmd="top"
            ;;
        req*)
            guessed="requeue"
            cmd="requeue"
            ;;
        su*)
            guessed="suspend"
            cmd="suspend"
            ;;
        *)
            ;;
    esac
    if [[ $i == $((COMP_CWORD)) ]]; then
        if [[ $guessed != "no" ]]; then
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            COMPREPLY=($(compgen -W "add autocomplete cancel_reboot change confreload create delete drain edit get help hold list list-resources ls modify new ping reboot reconfigure release remove requeue resume rm set show suspend takeover token top undrain update version -h -p -j -d -z -f -y -t -P -o --version --help --style --pretty --json --csv --delimiter --zebra --force-update --yes --dry-run --no-dry-run --cache-timeout --profile --profile-str --format --list-fields" -- "$cur"))
            return
        fi
    fi

    # Handle standalone commands that don't take resource arguments
    case "$cmd" in
        version|ping|reconfigure|takeover)
            # These commands take -v/--verbose and -h/--help options
            COMPREPLY=($(compgen -W "-v --verbose -h --help" -- "$cur"))
            return
            ;;
        token)
            # Token command takes lifespan= and username= options
            if [[ "$cur" == *=* ]]; then
                local key="${cur%%=*}"
                local val="${cur#*=}"
                case "$key" in
                    lifespan)
                        COMPREPLY=($(compgen -W "lifespan=1h lifespan=30m lifespan=1:00:00 lifespan=infinite" -- "$cur"))
                        ;;
                    username)
                        local users="$(_slurm_cache_users)"
                        COMPREPLY=($(compgen -W "${users// / username=}" -- "$cur"))
                        [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/username=}")
                        ;;
                esac
            else
                COMPREPLY=($(compgen -W "lifespan= username= -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        drain)
            # Drain command takes nodes, filters (with optional - prefix for exclusion),
            # and optional --reason/-r or reason=
            local cached_nodes="$(_slurm_cache_nodes)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--reason --verbose --help" -- "$cur"))
            elif [[ "$prev" == "-r" || "$prev" == "--reason" ]]; then
                # Reason value - no completion
                return
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${COMP_WORDS[COMP_CWORD-1]}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix (handle both "cur=not:filter=val" and bash splitting on =)
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:reservation" ]]; then
                local val="${cur#not:reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:reservation=}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "reservation" ]]; then
                local val="${cur#reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/reservation=}")
            else
                COMPREPLY=($(compgen -W "$cached_nodes $node_filters $neg_filters reason= -r --reason -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        undrain)
            # Undrain command takes nodes and filters (with optional - prefix for exclusion)
            local cached_nodes="$(_slurm_cache_nodes)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix (handle both "cur=not:filter=val" and bash splitting on =)
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:reservation" ]]; then
                local val="${cur#not:reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:reservation=}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "reservation" ]]; then
                local val="${cur#reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/reservation=}")
            else
                COMPREPLY=($(compgen -W "$cached_nodes $node_filters $neg_filters -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        reboot)
            # Reboot command takes nodes, filters, asap, nextstate=, reason=
            local cached_nodes="$(_slurm_cache_nodes)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            local nextstates="RESUME DOWN"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            elif [[ "$cur" == nextstate=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "nextstate" ]]; then
                local val="${cur#nextstate=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$nextstates" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/nextstate=}")
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${COMP_WORDS[COMP_CWORD-1]}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:reservation" ]]; then
                local val="${cur#not:reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:reservation=}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "reservation" ]]; then
                local val="${cur#reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/reservation=}")
            else
                COMPREPLY=($(compgen -W "ALL asap nextstate= reason= $cached_nodes $node_filters $neg_filters -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        cancel_reboot)
            # Cancel reboot command takes nodes and filters
            local cached_nodes="$(_slurm_cache_nodes)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:reservation" ]]; then
                local val="${cur#not:reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:reservation=}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "reservation" ]]; then
                local val="${cur#reservation=}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/reservation=}")
            else
                COMPREPLY=($(compgen -W "$cached_nodes $node_filters $neg_filters -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        hold)
            # Hold command takes job IDs and job filters, with optional reason
            local cached_jobs="$(_slurm_cache_jobs)"
            local cached_users="$(_slurm_cache_users)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local cached_accounts="$(_slurm_cache_accounts)"
            local job_filters="user= account= partition= state= name="
            local neg_job_filters="not:user= not:account= not:partition= not:state= not:name="
            local job_states="pending running suspended"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--reason --verbose --help" -- "$cur"))
            elif [[ "$cur" == -* && "${#cur}" -eq 2 ]]; then
                COMPREPLY=($(compgen -W "-r -v -h" -- "$cur"))
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${COMP_WORDS[COMP_CWORD-1]}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:account=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:account" ]]; then
                local val="${cur#not:account=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:account=}")
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            # Positive filters
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == account=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "account" ]]; then
                local val="${cur#account=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/account=}")
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            else
                COMPREPLY=($(compgen -W "$cached_jobs $job_filters $neg_job_filters reason= -r --reason -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        release|top|requeue|suspend)
            # Job control commands take job IDs and job filters
            local cached_jobs="$(_slurm_cache_jobs)"
            local cached_users="$(_slurm_cache_users)"
            local cached_partitions="$(_slurm_cache_partitions)"
            local cached_accounts="$(_slurm_cache_accounts)"
            local job_filters="user= account= partition= state= name="
            local neg_job_filters="not:user= not:account= not:partition= not:state= not:name="
            local job_states="pending running suspended"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:user" ]]; then
                local val="${cur#not:user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:user=}")
            elif [[ "$cur" == not:account=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:account" ]]; then
                local val="${cur#not:account=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:account=}")
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:partition" ]]; then
                local val="${cur#not:partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:partition=}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "not:state" ]]; then
                local val="${cur#not:state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/not:state=}")
            # Positive filters
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "user" ]]; then
                local val="${cur#user=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/user=}")
            elif [[ "$cur" == account=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "account" ]]; then
                local val="${cur#account=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/account=}")
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "partition" ]]; then
                local val="${cur#partition=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/partition=}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${COMP_WORDS[COMP_CWORD-2]}" == "state" ]]; then
                local val="${cur#state=}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${#COMPREPLY[@]} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${COMPREPLY[@]/#/state=}")
            else
                COMPREPLY=($(compgen -W "$cached_jobs $job_filters $neg_job_filters -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        autocomplete|help|list-resources)
            # These commands take -h/--help option
            COMPREPLY=($(compgen -W "-h --help" -- "$cur"))
            return
            ;;
    esac

    i=$((i+1))
    guessed="no"
    # Resource matching - generated from RESOURCES config
    case "$resource" in
        parti*|part|parts)
            guessed="partitions"
            ;;
        nodes|node)
            guessed="nodes"
            ;;
        jobs|job|j)
            guessed="jobs"
            ;;
        users|user)
            guessed="users"
            ;;
        qo*|q)
            guessed="qos"
            ;;
        accounts|acc|account)
            guessed="accounts"
            ;;
        associ*|assoc)
            guessed="associations"
            ;;
        reservations|reservation)
            guessed="reservations"
            ;;
        coordi*|coord)
            guessed="coordinators"
            ;;
        events|event|ev)
            guessed="events"
            ;;
        probl*|prob)
            guessed="problems"
            ;;
        stats|stat)
            guessed="stats"
            ;;
        confi*|conf|cf*)
            guessed="config"
            ;;
        licenses|lic|license)
            guessed="licenses"
            ;;
        dumps|dump)
            guessed="dumps"
            ;;
        resou*|reso)
            guessed="resources"
            ;;
        bads|bad|b)
            guessed="bads"
            ;;
        runawayj*|runaway|runa)
            guessed="runawayjobs"
            ;;
        tre*|tr)
            guessed="tres"
            ;;
        arc*|ar)
            guessed="archive"
            ;;
        transa*|tra|trans)
            guessed="transactions"
            ;;
    esac

    # echo "i=$i j=$j COMP_CWORD=$COMP_CWORD \
    # guessed=$guessed resource=$resource"

    # If resource is empty or we're completing the resource position,
    # show resource list
    if [[ -z "$resource" ]] || [[ $j -ge $COMP_CWORD ]]; then
        if [[ $guessed != "no" ]]; then
            # Events are read-only, don't suggest for update/delete
            if [[ "$guessed" == "events" ]] && [[ "$cmd" == "update" || "$cmd" == "delete" ]]; then
                return
            fi
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            # Base resources for all commands
            local all_resources="reservations nodes partitions accounts \
                qos users coordinators problems stats associations dumps \
                licenses bad runawayjobs tres archives transactions jobs"
            # Events are read-only, only available for show command
            if [[ "$cmd" == "show" ]]; then
                all_resources="$all_resources events"
            fi
            COMPREPLY=($(compgen -W "$all_resources" -- "$cur"))
            return
        fi
    fi

    # Handle options that come after the resource
    # Check if previous word needs a value
    case "$prev" in
        --style)
            COMPREPLY=($(compgen -W "pretty json csv" -- "$cur"))
            return
            ;;
        --profile|-P)
            # Profile names - built-in plus any from config files
            local profiles="default compact minimal oneline detailed"
            if [ -f "$HOME/.config/slurm-cli.profiles" ]; then
                local user_profiles=$(grep -oE '^[a-z_]+:' "$HOME/.config/slurm-cli.profiles" 2>/dev/null | tr -d ':' | tr '\n' ' ')
                profiles="$profiles $user_profiles"
            fi
            if [ -f "/etc/slurm/cli.profiles" ]; then
                local sys_profiles=$(grep -oE '^[a-z_]+:' "/etc/slurm/cli.profiles" 2>/dev/null | tr -d ':' | tr '\n' ' ')
                profiles="$profiles $sys_profiles"
            fi
            COMPREPLY=($(compgen -W "$profiles" -- "$cur"))
            return
            ;;
        =)
            # Handle --profile=value format (when = is a separate word)
            if [[ ${COMP_CWORD} -ge 2 ]]; then
                local opt="${COMP_WORDS[COMP_CWORD-2]}"
                if [[ "$opt" == "--profile" || "$opt" == "-P" ]]; then
                    local profiles="default compact minimal oneline detailed"
                    if [ -f "$HOME/.config/slurm-cli.profiles" ]; then
                        local user_profiles=$(grep -oE '^[a-z_]+:' "$HOME/.config/slurm-cli.profiles" 2>/dev/null | tr -d ':' | tr '\n' ' ')
                        profiles="$profiles $user_profiles"
                    fi
                    if [ -f "/etc/slurm/cli.profiles" ]; then
                        local sys_profiles=$(grep -oE '^[a-z_]+:' "/etc/slurm/cli.profiles" 2>/dev/null | tr -d ':' | tr '\n' ' ')
                        profiles="$profiles $sys_profiles"
                    fi
                    COMPREPLY=($(compgen -W "$profiles" -- "$cur"))
                    return
                fi
            fi
            ;;
        --delimiter|-d|--cache-timeout|-t)
            # These options need a value, no completion
            return
            ;;
        --profile-str|--format|-o)
            # Complete with available fields for the resource
            local fields=""
            case "$guessed" in
                jobs) fields="job_id name user_name account partition job_state time_limit endlimit node_count nodes cpus gres submit_time start_time end_time priority reason command working_directory" ;;
                nodes) fields="name state cpus real_memory gres partitions features reason alloc_cpus alloc_memory" ;;
                partitions) fields="partitionname state nodes totalnodes totalcpus maxtime default defaulttime defmempercpu defmempernode allowgroups allowaccounts allowqos denyaccounts denyqos maxnodes minnodes maxcpuspernode maxcpuspersocket maxmempercpu maxmempernode prioritytier priorityjobfactor preemptmode gracetime oversubscribe overtimelimit qos alternate allocnodes cpubind disablerootjobs exclusiveuser hidden jobdefaults lln powerdownonidle reqresv rootonly shared tresbillingweights" ;;
                accounts) fields="name description organization coordinators flags" ;;
                users) fields="name default_account admin_level coordinators" ;;
                qos) fields="name id priority max_wall max_jobs max_submit flags preempt preempt_mode grace_time" ;;
                reservations) fields="name start_time end_time nodes users accounts partition state flags" ;;
                associations) fields="account user cluster partition parent_account qos default_qos shares grp_jobs grp_submit" ;;
                coordinators) fields="account name" ;;
                events) fields="time cluster node state reason user" ;;
            esac
            if [[ -n "$fields" ]]; then
                # Handle comma-separated fields: filter out already selected ones
                local prefix="" partial=""
                if [[ "$cur" == *,* ]]; then
                    prefix="${cur%,*},"
                    partial="${cur##*,}"
                    # Filter out already selected fields
                    local selected="${cur%,*}"
                    local remaining=""
                    for f in $fields; do
                        if [[ ",$selected," != *",$f,"* ]]; then
                            remaining="$remaining $f"
                        fi
                    done
                    fields="$remaining"
                else
                    partial="$cur"
                fi
                COMPREPLY=($(compgen -W "$fields" -- "$partial"))
                # Add prefix to each completion
                if [[ -n "$prefix" ]]; then
                    COMPREPLY=("${COMPREPLY[@]/#/$prefix}")
                fi
            fi
            return
            ;;
    esac

    # If current word starts with -, show options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "-h -p -j -d -z -f -y -t -P -o --version --help --style --pretty --json --csv --delimiter --zebra --force-update --yes --dry-run --no-dry-run --cache-timeout --profile --profile-str --format --list-fields" -- "$cur"))
        return
    fi

    # command current_autocomplete_word_index
    # Use guessed (full name) instead of resource (partial name)
    # Check if the autocomplete function exists before calling it
    if type "_slurm_cli_${guessed}_autocomplete" &>/dev/null; then
        _slurm_cli_${guessed}_autocomplete "$cmd" "$j"
    fi

    # echo "${COMP_REPLY[@]}"
}


# ==============================================================================
# Common autocomplete helper functions
# ==============================================================================

# Cache timeout in seconds
_SLURM_CACHE_TIMEOUT=600

# Check if cache update is disabled via environment variable
# Returns 0 if updates are disabled, 1 otherwise
_slurm_cache_updates_disabled() {
    local val="${SLURM_CLI_NO_CACHE_UPDATE:-}"
    val="${val,,}"  # lowercase
    [[ "$val" == "1" || "$val" == "y" || "$val" == "yes" || "$val" == "true" ]]
}

# Ensure cache file exists and is fresh, update if needed
# Usage: _slurm_ensure_cache "/tmp/slurm_cli_nodes.json" "nodes"
_slurm_ensure_cache() {
    local file="$1"
    local resource="$2"

    # Skip if updates are disabled
    _slurm_cache_updates_disabled && return

    local needs_update=0

    if [[ ! -f "$file" ]]; then
        needs_update=1
    else
        # Check if file is older than timeout
        local now=$(date +%s)
        local mtime=$(stat -c %Y "$file" 2>/dev/null || echo 0)
        local age=$((now - mtime))
        if [[ $age -gt $_SLURM_CACHE_TIMEOUT ]]; then
            needs_update=1
        fi
    fi

    if [[ $needs_update -eq 1 ]]; then
        # Update cache silently in foreground (need results immediately)
        slurm-cli show "$resource" --style=json >/dev/null 2>&1
    fi
}

# Complete with compgen, handling empty current word
# Usage: _slurm_complete "word1 word2 word3" "$cur"
_slurm_complete() {
    local words="$1"
    local cur="$2"
    if [[ -z "$cur" ]]; then
        COMPREPLY=($(compgen -W "$words"))
    else
        COMPREPLY=($(compgen -W "$words" -- "$cur"))
    fi
}

# Get names from a JSON cache file
# Usage: _slurm_cache_get "/tmp/file.json" ".field[].name" -> "name1 name2 name3"
_slurm_cache_get() {
    local file="$1"
    local jq_expr="$2"
    if [ -f "$file" ]; then
        jq -r "$jq_expr" "$file" 2>/dev/null | tr '\n' ' '
    fi
}

# Parse key=value format and set _key and _val variables
# Usage: _slurm_parse_keyval "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part
#        Returns: 0 if key=value found, 1 otherwise
_slurm_parse_keyval() {
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""

    if [[ $cur == = ]]; then
        # cur is just "=", key is previous word
        _key="${prev,,}"
        _val=""
        return 0
    elif [[ $cur == *=* ]]; then
        # cur contains "=" (e.g., "key=val" or "key=")
        _key="${cur%%=*}"
        _key="${_key,,}"
        _val="${cur#*=}"
        return 0
    elif [[ $prev == = ]]; then
        # prev is "=", key is two words back
        _key="${COMP_WORDS[COMP_CWORD-2]}"
        _key="${_key,,}"
        _val="$cur"
        return 0
    fi
    return 1
}

# Parse key=value, key+=value, or key-=value format
# Usage: _slurm_parse_keyval_ext "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part, $_op = operator (=, +=, -=)
#        Returns: 0 if found, 1 otherwise
_slurm_parse_keyval_ext() {
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""
    _op=""

    # Check cur for key+=val, key-=val, or key=val
    if [[ $cur == *[-+]=* ]] || [[ $cur == *=* ]]; then
        _key="${cur%%[-+]*=*}"
        _key="${_key%%=*}"
        _key="${_key,,}"
        _val="${cur#*=}"
        [[ $cur == *+=* ]] && _op="+=" || { [[ $cur == *-=* ]] && _op="-=" || _op="="; }
        return 0
    # Check if prev is =, +=, or -=
    elif [[ $prev == "=" ]] || [[ $prev == "+=" ]] || [[ $prev == "-=" ]]; then
        _key="${COMP_WORDS[COMP_CWORD-2]}"
        _key="${_key,,}"
        _val="$cur"
        _op="$prev"
        return 0
    # Check if prev ends with operator
    elif [[ $prev == *[-+]= ]] || [[ $prev == *= ]]; then
        _key="${prev%%[-+]*=}"
        _key="${_key%%=}"
        _key="${_key,,}"
        _val="$cur"
        _op="${prev##*[!-+=]}"
        return 0
    fi
    return 1
}

# Complete value and add key= (or key+= / key-=) prefix back if needed
# Usage: _slurm_complete_value "word1 word2" "$_key" "$_val" "$cur"
#        If cur contains =, prefix is added back to completions
#        If prev is = (bash split on =), do NOT add prefix (it's already typed)
#        Uses $_op if set by _slurm_parse_keyval_ext (defaults to "=")
_slurm_complete_value() {
    local words="$1"
    local key="$2"
    local val="$3"
    local cur="$4"
    local op="${_op:-=}"

    COMPREPLY=($(compgen -W "$words" -- "$val"))

    # Only add key+op prefix when cur contains = (bash didn't split)
    # If bash split on =, the key= is already on command line
    if [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]]; then
        COMPREPLY=("${COMPREPLY[@]/#/$key$op}")
    fi
}

# Cache accessor functions for common resources
# Each function ensures cache is fresh before reading
_slurm_cache_accounts() {
    _slurm_ensure_cache "/tmp/slurm_cli_accounts.json" "accounts"
    _slurm_cache_get "/tmp/slurm_cli_accounts.json" '.accounts[].name'
}

_slurm_cache_qos() {
    _slurm_ensure_cache "/tmp/slurm_cli_qos.json" "qos"
    _slurm_cache_get "/tmp/slurm_cli_qos.json" '.qos[].name'
}

_slurm_cache_partitions() {
    _slurm_ensure_cache "/tmp/slurm_cli_partitions.json" "partitions"
    _slurm_cache_get "/tmp/slurm_cli_partitions.json" 'keys[]'
}

_slurm_cache_nodes() {
    _slurm_ensure_cache "/tmp/slurm_cli_nodes.json" "nodes"
    _slurm_cache_get "/tmp/slurm_cli_nodes.json" 'keys[]'
}

_slurm_cache_users() {
    _slurm_ensure_cache "/tmp/slurm_cli_users.json" "users"
    _slurm_cache_get "/tmp/slurm_cli_users.json" '.users[].name'
}

_slurm_cache_reservations() {
    _slurm_ensure_cache "/tmp/slurm_cli_reservations.json" "reservations"
    _slurm_cache_get "/tmp/slurm_cli_reservations.json" 'keys[]'
}

_slurm_cache_jobs() {
    _slurm_ensure_cache "/tmp/slurm_cli_jobs.json" "jobs"
    _slurm_cache_get "/tmp/slurm_cli_jobs.json" '.jobs[].job_id'
}

# Node filter prefixes for nodes= parameter
# Supports: ALL, partition=, state=, user=, reservation=
_slurm_node_filter_prefixes="ALL partition= state= user= reservation="

# Complete nodes= value with either direct nodes or filter prefixes
# Usage: _slurm_complete_nodes_value "$_val" "$cur" ["$_key"]
# The prefix for completions is derived from $cur to preserve case
_slurm_complete_nodes_value() {
    local val="$1"
    local cur="$2"
    local key="${3:-nodes}"
    local cached_nodes="$(_slurm_cache_nodes)"

    # Derive prefix from cur by removing val from the end (preserves original case)
    # Note: When bash splits on '=', cur is empty and we should NOT add prefix
    # because bash already has the key= part typed
    local prefix=""
    if [[ "$cur" == *=* && -n "$val" ]]; then
        prefix="${cur%"$val"}"
    elif [[ "$cur" == *=* ]]; then
        prefix="$cur"
    fi

    # Check if value starts with a filter prefix
    if [[ "$val" == partition=* ]]; then
        local filter_val="${val#partition=}"
        local partitions="$(_slurm_cache_partitions)"
        COMPREPLY=($(compgen -W "$partitions" -- "$filter_val"))
        [[ -n "$prefix" && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/${prefix}partition=}")
    elif [[ "$val" == state=* ]]; then
        local filter_val="${val#state=}"
        local states="idle alloc drain down mixed comp"
        COMPREPLY=($(compgen -W "$states" -- "$filter_val"))
        [[ -n "$prefix" && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/${prefix}state=}")
    elif [[ "$val" == user=* ]]; then
        local filter_val="${val#user=}"
        local users="$(_slurm_cache_users)"
        COMPREPLY=($(compgen -W "$users" -- "$filter_val"))
        [[ -n "$prefix" && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/${prefix}user=}")
    elif [[ "$val" == reservation=* ]]; then
        local filter_val="${val#reservation=}"
        local reservations="$(_slurm_cache_reservations)"
        COMPREPLY=($(compgen -W "$reservations" -- "$filter_val"))
        [[ -n "$prefix" && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/${prefix}reservation=}")
    else
        # Not a filter prefix, show filter prefixes and cached nodes
        COMPREPLY=($(compgen -W "$_slurm_node_filter_prefixes $cached_nodes" -- "$val"))
        [[ ${#COMPREPLY[@]} -gt 0 && -n "$prefix" ]] && COMPREPLY=("${COMPREPLY[@]/#/$prefix}")
    fi
}


_slurm_cli_reservations_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local name="${COMP_WORDS[$pos]}"

    local cached_reservations="$(_slurm_cache_reservations)"
    local options="accounts= burstbuffer= corecnt= licenses= maxstartdelay= nodecnt= nodes= starttime= endtime= duration= partitionname= flags= features= groups= skip= users= tres= trespernode= start= end= nodes+= nodes-="

    # First argument after 'reservations'
    if [[ $name == reservations && $prev == reservations ]]; then
        _slurm_complete "$cached_reservations" "$cur"
        return
    fi

    case "$cmd" in
        show|delete) return ;;
        create|update)
            if _slurm_parse_keyval "$cur" "$prev"; then
                local -A valid_types=([accounts]="list" [burstbuffer]="list" [corecnt]="int" [licenses]="list" [maxstartdelay]="time" [nodecnt]="int" [nodes]="nodes" [starttime]="time" [endtime]="time" [duration]="time" [partitionname]="partition" [flags]="list" [features]="list" [groups]="list" [skip]="[yes, no, y, n, 1, 0]" [users]="list" [tres]="list" [trespernode]="list" [start]="time" [end]="time")
                local type=${valid_types[$_key]}
                # Handle nodes+ and nodes- specially
                [[ "$_key" == "nodes+" || "$_key" == "nodes-" ]] && type="nodes"
                case "$type" in
                    nodes)
                        _slurm_complete_nodes_value "$_val" "$cur" "$_key" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    account)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    int|time) ;;
                    *)
                        case "$_key" in
                            flags)
                                _slurm_complete_value "ANY_NODES DAILY FLEX IGNORE_JOBS HOURLY LICENSE_ONLY MAINT MAGNETIC NO_HOLD_JOBS_AFTER OVERLAP PART_NODES PURGE_COMP REPLACE REPLACE_DOWN SPEC_NODES STATIC_ALLOC TIME_FLOAT WEEKDAY WEEKEND WEEKLY" "$_key" "$_val" "$cur" ;;
                            skip)
                                _slurm_complete_value "yes no y n 1 0" "$_key" "$_val" "$cur" ;;
                            state)
                                # Node filter: nodes=state=<state>
                                local states="idle alloc drain down mixed comp"
                                COMPREPLY=($(compgen -W "$states" -- "$_val"))
                                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=state=}")
                                ;;
                            partition)
                                # Node filter: nodes=partition=<partition>
                                COMPREPLY=($(compgen -W "$(_slurm_cache_partitions)" -- "$_val"))
                                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=partition=}")
                                ;;
                            user)
                                # Node filter: nodes=user=<user>
                                COMPREPLY=($(compgen -W "$(_slurm_cache_users)" -- "$_val"))
                                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=user=}")
                                ;;
                            reservation)
                                # Node filter: nodes=reservation=<reservation>
                                COMPREPLY=($(compgen -W "$cached_reservations" -- "$_val"))
                                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=reservation=}")
                                ;;
                        esac
                        ;;
                esac
                return
            fi
            _slurm_complete "$options" "$cur"
            ;;
    esac
}


_slurm_cli_qos_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local name="${COMP_WORDS[$pos]}"

    local cached_qos="$(_slurm_cache_qos)"
    local options="description= flags= gracetime= grpjobs= grpjobsaccrue= grpsubmit= grpsubmitjobs= grptres= grptresmins= grptresrunmins= grpwall= limitfactor= maxjobsaccruepa= maxjobsaccrueperaccount= maxjobsaccruepu= maxjobsaccrueperuser= maxjobspa= maxjobsperaccount= maxjobspu= maxjobsperuser= maxsubmitjobspa= maxsubmitjobsperaccount= maxsubmitjobspu= maxsubmitjobsperuser= maxtres= maxtrespj= maxtresperjob= maxtresmins= maxtresminspj= maxtresminsperjob= maxtrespa= maxtresperaccount= maxtrespn= maxtrespernode= maxtrespu= maxtresperuser= maxtresrunminspa= maxtresrunminsperaccount= maxtresrunminspu= maxtresrunminsperuser= maxwall= maxwalldurationperjob= minpriothreshold= mintres= mintresperjob= name= preempt= preemptexempttime= preemptmode= priority= rawusage= usagefactor= usagethreshold="

    # First argument after 'qos'
    if [[ $name == qos && $prev == qos ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$options $cached_qos" "$cur" ;;
            create|update) _slurm_complete "$options $cached_qos" "$cur" ;;
        esac
        return
    fi

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            flags)
                _slurm_complete_value "DenyOnLimit EnforceUsageThreshold NoDecay NoReserve OverPartQOS PartitionMaxNodes PartitionMinNodes PartitionTimeLimit Relative RequiresReservation UsageFactorSafe" "$_key" "$_val" "$cur" ;;
            preemptmode)
                _slurm_complete_value "OFF CANCEL GANG REQUEUE SUSPEND WITHIN" "$_key" "$_val" "$cur" ;;
            preempt|name)
                _slurm_complete_value "$cached_qos" "$_key" "$_val" "$cur" ;;
        esac
        return
    fi

    # Complete option names
    case "$cmd" in
        show|delete) _slurm_complete "$options" "$cur" ;;
        create|update) _slurm_complete "$options" "$cur" ;;
    esac
}


_slurm_cli_accounts_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local name="${COMP_WORDS[$pos]}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local filter_options="cluster= description= name= organization= parent= rawusage="
    local update_options="$filter_options set"

    # First argument after 'accounts' (not completing a value)
    if [[ $name == accounts && $prev == accounts && $cur != *=* ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_accounts" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_accounts" "$cur" ;;
        esac
        return
    fi

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            defaultqos)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            parent|organization|name)
                _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
        esac
        return
    fi

    # Complete option names
    case "$cmd" in
        show|delete) _slurm_complete "$filter_options" "$cur" ;;
        create|update) _slurm_complete "$update_options" "$cur" ;;
    esac
}


_slurm_cli_associations_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local name="${COMP_WORDS[$pos]}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local cached_users="$(_slurm_cache_users)"
    local filter_options="account= cluster= partition= user="
    local set_options="defaultqos= fairshare= share= grpjobs= grpjobsaccrue= grpsubmit= grpsubmitjobs= grptres= grptresmins= grptresrunmins= grpwall= maxjobs= maxjobsaccrue= maxsubmit= maxsubmitjobs= maxtres= maxtrespj= maxtresperjob= maxtresmins= maxtresminspj= maxtresminsperjob= maxtrespn= maxtrespernode= maxwall= maxwalldurationperjob= priority= qoslevel= qoslevel+= qoslevel-="
    local update_options="$filter_options $set_options set"
    local create_options="$filter_options $set_options"

    # Handle key=value, key+=value, or key-=value completion
    if _slurm_parse_keyval_ext "$cur" "$prev"; then
        case "$_key" in
            account)
                _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
            user)
                _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
            defaultqos|qos|qoslevel)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    # First argument after 'associations'
    if [[ $name == associations && $prev == associations ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_accounts" "$cur" ;;
            create)      _slurm_complete "$create_options" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_accounts" "$cur" ;;
        esac
        return
    fi

    # Default completion for subsequent arguments
    case "$cmd" in
        show|delete) _slurm_complete "$filter_options" "$cur" ;;
        create)      _slurm_complete "$create_options" "$cur" ;;
        update)      _slurm_complete "$update_options" "$cur" ;;
    esac
}


_slurm_cli_coordinators_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local cached_users="$(_slurm_cache_users)"
    local options="account= user= name="

    # Handle key=value completion for current word
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            account) _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
            name|user) _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    # For create, check what's already been specified
    if [[ "$cmd" == "create" ]]; then
        local has_account=false
        local has_user=false
        local has_positional_user=false

        # Scan previous words to see what's already specified
        for ((i=pos+1; i<COMP_CWORD; i++)); do
            local word="${COMP_WORDS[$i]}"
            if [[ "$word" == account=* ]]; then
                has_account=true
            elif [[ "$word" == name=* || "$word" == user=* ]]; then
                has_user=true
            elif [[ "$word" != *=* && "$word" != -* ]]; then
                # Positional argument (user)
                has_positional_user=true
            fi
        done

        # First arg after coordinators: show options + users
        if [[ $prev == coordinators || $prev == coord ]]; then
            _slurm_complete "$options $cached_users" "$cur"
            return
        fi

        # After user= or positional user: suggest account=
        if $has_user || $has_positional_user; then
            if ! $has_account; then
                _slurm_complete "$options" "$cur"
                return
            fi
        fi

        # After account=: suggest user= with users
        if $has_account; then
            if ! $has_user && ! $has_positional_user; then
                _slurm_complete "$options $cached_users" "$cur"
                return
            fi
        fi

        # Default: show all options
        _slurm_complete "$options $cached_users" "$cur"
        return
    fi

    # For show/delete
    if [[ $prev == coordinators || $prev == coord ]]; then
        _slurm_complete "$options $cached_accounts $cached_users" "$cur"
    else
        _slurm_complete "$options" "$cur"
    fi
}


_slurm_cli_events_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local filter_options="Clusters= CondFlags= End= Events= MaxCPUs= MinCPUs= MaxNodes= MinNodes= Nodes= Reason= Start= States= User="

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            condflags)
                _slurm_complete_value "Open" "$_key" "$_val" "$cur" ;;
            states)
                _slurm_complete_value "DOWN DRAIN FAIL FUTR IDLE MAINT POWER REBOOT" "$_key" "$_val" "$cur" ;;
            events)
                _slurm_complete_value "Cluster Node" "$_key" "$_val" "$cur" ;;
            nodes)
                _slurm_complete_nodes_value "$_val" "$cur" "$_key" ;;
            clusters)
                # Note: clusters don't have a cache, so no value completion
                ;;
            user)
                local cached_users="$(_slurm_cache_users)"
                _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
            # Node filter nested keys (when = is a word break, these are parsed as top-level keys)
            partition)
                _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
            state)
                _slurm_complete_value "idle alloc drain down mixed comp" "$_key" "$_val" "$cur" ;;
            reservation)
                _slurm_complete_value "$(_slurm_cache_reservations)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    # Default: show filter options
    [[ $cmd == "show" ]] && _slurm_complete "$filter_options" "$cur"
}


_slurm_cli_jobs_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    local filter_options="job_id= user= account= partition= state= name= nodes= reservation="
    local update_options="contiguous= oversubscribe= reboot= shared= requeue= arraytaskthrottle= corespec= cpuspertask= mincpusnode= minmemorycpu= minmemorynode= mintmpdisknode= nice= numcpus= numnodes= numtasks= priority= reqcores= reqnodes= reqprocs= reqsockets= reqthreads= sitefactor= switches= taskspernode= threadspec= deadline= delayboot= eligibletime= endtime= starttime= timelimit= timemin= excnodelist= nodelist= reqnodelist= partition= qos= account= reservationname= mailuser= userid= admincomment= burstbuffer= clusters= clusterfeatures= comment= dependency= extra= features= gres= jobname= licenses= mailtype= name= prefer= stderr= stdin= stdout= wckey= workdir= resetaccruetime"

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            # Filter options
            job_id|jobid)
                _slurm_complete_value "$(_slurm_cache_jobs)" "$_key" "$_val" "$cur" ;;
            state)
                _slurm_complete_value "pending running cancelled completing completed boot_fail configuring deadline failed node_fail out_of_memory preempted resv_del_hold requeue_fed requeue_hold requeued resizing revoked signaling special_exit stage_out stopped suspended timeout" "$_key" "$_val" "$cur" ;;
            user|mailuser|userid)
                _slurm_complete_value "$(_slurm_cache_users)" "$_key" "$_val" "$cur" ;;
            account)
                _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
            nodes|nodelist|excnodelist|reqnodelist)
                _slurm_complete_nodes_value "$_val" "$cur" "$_key" ;;
            reservation|reservationname)
                _slurm_complete_value "$(_slurm_cache_reservations)" "$_key" "$_val" "$cur" ;;
            qos)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            name|jobname)
                # No completion for free-form text
                return ;;
            # Yes/No options
            contiguous|oversubscribe|reboot|shared)
                _slurm_complete_value "yes no" "$_key" "$_val" "$cur" ;;
            # 0/1 options
            requeue)
                _slurm_complete_value "0 1" "$_key" "$_val" "$cur" ;;
            # Mail type
            mailtype)
                _slurm_complete_value "NONE BEGIN END FAIL REQUEUE ALL INVALID_DEPEND STAGE_OUT TIME_LIMIT TIME_LIMIT_90 TIME_LIMIT_80 TIME_LIMIT_50 ARRAY_TASKS" "$_key" "$_val" "$cur" ;;
            # Dependency
            dependency)
                _slurm_complete_value "after: afterany: afternotok: afterok: singleton" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    local cached_jobs="$(_slurm_cache_jobs)"

    # Default: show options and job IDs based on command
    case "$cmd" in
        show)
            _slurm_complete "$filter_options" "$cur" ;;
        delete|del|cancel)
            _slurm_complete "$filter_options $cached_jobs" "$cur" ;;
        update|modify|set)
            _slurm_complete "$update_options $filter_options $cached_jobs" "$cur" ;;
    esac
}


_slurm_cli_users_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local name="${COMP_WORDS[$pos]}"

    local cached_users="$(_slurm_cache_users)"
    local filter_options="account= adminlevel= cluster= defaultaccount= defaultwckey= name= partition= qos="
    local where_options="account= adminlevel= cluster= defaultaccount= defaultwckey= name= partition="
    local set_options="adminlevel= defaultaccount= defaultwckey= newname= partition= fairshare="
    local create_options="name= account= adminlevel= cluster= defaultaccount= defaultwckey= partition= rawusage="
    local update_options="$cached_users $where_options set"

    # Check if 'set' keyword has been typed
    local found_set=0
    for word in "${COMP_WORDS[@]}"; do
        [[ "$word" == "set" ]] && found_set=1 && break
    done

    # First argument after 'users'
    if [[ $name == users && $prev == users ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_users" "$cur" ;;
            create)      _slurm_complete "$create_options" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_users" "$cur" ;;
        esac
        return
    fi

    case "$cmd" in
        delete)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "None Admin Operator" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$filter_options" "$cur"
            return
            ;;
        update)
            # After 'set' keyword, show SET options
            if [[ $found_set -eq 1 ]]; then
                if _slurm_parse_keyval "$cur" "$prev"; then
                    case "$_key" in
                        adminlevel)
                            _slurm_complete_value "None Admin Operator" "$_key" "$_val" "$cur" ;;
                        newname|name)
                            _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                        defaultaccount)
                            _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                        partition)
                            _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    esac
                    return
                fi
                _slurm_complete "$set_options" "$cur"
                return
            fi
            # Before 'set' keyword, show WHERE options and 'set'
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "None Admin Operator" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$where_options set" "$cur"
            return
            ;;
        show)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    qos)
                        _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "None Admin Operator" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$filter_options" "$cur"
            ;;
        create)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "None Admin Operator" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$create_options" "$cur"
            ;;
    esac
}


_slurm_cli_partitions_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    local cached_partitions="$(_slurm_cache_partitions)"
    local options="allocnodes= allowaccounts= allowgroups= allowqos= alternate= cpubind= default= defaulttime= defmempercpu= defmempernode= denyaccounts= denyqos= disablerootjobs= exclusiveuser= gracetime= hidden= jobdefaults= lln= maxcpuspernode= maxcpuspersocket= maxmempercpu= maxmempernode= maxnodes= maxtime= minnodes= nodes= oversubscribe= overtimelimit= powerdownonidle= preemptmode= priority= priorityjobfactor= prioritytier= qos= reqresv= rootonly= tresbillingweights= partitionname= shared= state= nodes+= nodes-="

    # First argument after 'partitions'
    if [[ $prev == partitions || $prev == part || $prev == parts ]]; then
        case "$cmd" in
            show|delete|update|modify|set) _slurm_complete "$cached_partitions $options" "$cur" ;;
            create|add|new) _slurm_complete "$options" "$cur" ;;
        esac
        return
    fi

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        # Check if we're in a node filter context by checking COMP_LINE
        local in_node_filter=false
        [[ "$COMP_LINE" == *nodes=state=* || "$COMP_LINE" == *nodes=partition=* ||            "$COMP_LINE" == *nodes=user=* || "$COMP_LINE" == *nodes=reservation=* ||            "$COMP_LINE" == *Nodes=state=* || "$COMP_LINE" == *Nodes=partition=* ||            "$COMP_LINE" == *Nodes=user=* || "$COMP_LINE" == *Nodes=reservation=* ||            "$COMP_LINE" == *nodes+=state=* || "$COMP_LINE" == *nodes+=partition=* ||            "$COMP_LINE" == *nodes+=user=* || "$COMP_LINE" == *nodes+=reservation=* ||            "$COMP_LINE" == *nodes-=state=* || "$COMP_LINE" == *nodes-=partition=* ||            "$COMP_LINE" == *nodes-=user=* || "$COMP_LINE" == *nodes-=reservation=* ]] && in_node_filter=true

        case "$_key" in
            state)
                if $in_node_filter; then
                    # Node filter: nodes=state=<state>
                    local node_states="idle alloc drain down mixed comp"
                    COMPREPLY=($(compgen -W "$node_states" -- "$_val"))
                    [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=state=}")
                else
                    # Partition state
                    _slurm_complete_value "up down drain inactive UP DOWN DRAIN INACTIVE" "$_key" "$_val" "$cur"
                fi
                ;;
            preemptmode)
                _slurm_complete_value "off cancel requeue suspend OFF CANCEL REQUEUE SUSPEND" "$_key" "$_val" "$cur" ;;
            cpubind)
                _slurm_complete_value "none socket ldom core thread off" "$_key" "$_val" "$cur" ;;
            default|disablerootjobs|exclusiveuser|hidden|lln|oversubscribe|powerdownonidle|reqresv|rootonly|shared)
                _slurm_complete_value "yes no YES NO" "$_key" "$_val" "$cur" ;;
            allowaccounts|denyaccounts)
                _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
            allowqos|denyqos|qos)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            nodes|nodes+|nodes-)
                _slurm_complete_nodes_value "$_val" "$cur" "$_key" ;;
            alternate|partitionname)
                _slurm_complete_value "$cached_partitions" "$_key" "$_val" "$cur" ;;
            partition)
                # Node filter: nodes=partition=<partition>
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$_val"))
                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=partition=}")
                ;;
            user)
                # Node filter: nodes=user=<user>
                COMPREPLY=($(compgen -W "$(_slurm_cache_users)" -- "$_val"))
                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=user=}")
                ;;
            reservation)
                # Node filter: nodes=reservation=<reservation>
                COMPREPLY=($(compgen -W "$(_slurm_cache_reservations)" -- "$_val"))
                [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]] && COMPREPLY=("${COMPREPLY[@]/#/nodes=reservation=}")
                ;;
        esac
        return
    fi

    # Complete option names
    _slurm_complete "$options" "$cur"
}


_slurm_cli_nodes_autocomplete() {
    local cmd="$1"
    local pos="$2"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    local cached_nodes="$(_slurm_cache_nodes)"
    local cached_partitions="$(_slurm_cache_partitions)"
    local show_options="name= state= partition= features= gres="
    local update_options="nodename= activefeatures= availablefeatures= comment= cpubind= extra= gres= instanceid= instancetype= nodeaddr= nodehostname= reason= resumeafter= state= weight="
    local filter_options="ALL partition= state= user= reservation= drainreason="
    local neg_filter_options="not:partition= not:state= not:user= not:reservation= not:drainreason="
    local create_options="state= cpus= features= gres= reason= weight="

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            state)
                # Different states for create vs update
                if [[ "$cmd" == "create" ]]; then
                    _slurm_complete_value "future cloud" "$_key" "$_val" "$cur"
                elif [[ "$cmd" == "update" ]]; then
                    _slurm_complete_value "cancel_reboot down drain fail future idle noresp resume undrain" "$_key" "$_val" "$cur"
                else
                    _slurm_complete_value "idle alloc drain down resume undrain fail power_down power_up" "$_key" "$_val" "$cur"
                fi
                ;;
            cpubind)
                _slurm_complete_value "none socket ldom core thread off" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$cached_partitions" "$_key" "$_val" "$cur" ;;
            name|nodename)
                _slurm_complete_value "$cached_nodes" "$_key" "$_val" "$cur" ;;
            user)
                # Node filter: show users for selecting nodes by user's jobs
                _slurm_complete_value "$(_slurm_cache_users)" "$_key" "$_val" "$cur" ;;
            reservation)
                # Node filter: show reservations for selecting nodes
                _slurm_complete_value "$(_slurm_cache_reservations)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    # For show command: filter options, show options, then node names
    if [[ "$cmd" == "show" ]]; then
        _slurm_complete "$filter_options $neg_filter_options $show_options $cached_nodes" "$cur"
        return
    fi

    # For create command: show create options (name is positional)
    if [[ "$cmd" == "create" ]]; then
        _slurm_complete "$create_options" "$cur"
        return
    fi

    # For update command: filter options, update options, then node names
    if [[ "$cmd" == "update" ]]; then
        _slurm_complete "$filter_options $update_options $cached_nodes" "$cur"
        return
    fi

    # Default: show node names
    _slurm_complete "$cached_nodes" "$cur"
}


# Register the completion function for various invocation methods
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete slurm-cli
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete ./slurm-cli
    
