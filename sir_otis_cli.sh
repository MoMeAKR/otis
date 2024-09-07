#!/bin/bash 


add_arg() {
    command="$1"
    arg_name="$2"
    arg_value="$3"
    if [ -n "$arg_value" ] && [ $arg_value != "None" ]; then
        command="$command, $arg_name=\"$arg_value\""
    fi

    echo "$command"
}

make_command(){

    func_to_call="$1"
    local_fp="$2"
    base_contents_path="$3"
    struct_file="$4"
    interactive_graph="$5"

    command="python -c 'import sir_otis; sir_otis.$func_to_call(\"$local_fp\""
    
    if [ $func_to_call = "initial_build" ]; then
        if [ -e "$base_contents_path" ]; then
            command="$command, base_contents_path=\"$base_contents_path\""
        fi
    else
        command=$(add_arg "$command" "base_contents_path" "$base_contents_path")
    fi 
    # command=$(add_arg "$command" "base_contents_path" "$sys_desc")
    command=$(add_arg "$command" "structure_file" "$struct_file")
    command=$(add_arg "$command" "interactive_graph_path" "$interactive_graph")
    command="$command)'"
    echo $command
}


# local_file_path=$(dirname $0)/sir_otis_config.json
fp="$(python -c 'import sir_otis; print(sir_otis.__file__)')"
dn="$(dirname $fp)"
local_file_path="$dn/sir_otis_config.json"


if [ "$1" = "reset" ]; then 
    rm $local_file_path
    echo "Removed the local configuration file"
fi
if [ ! -e $local_file_path ]; then 
    python -c "import sir_otis; sir_otis.init_config_file('$local_file_path')"
    echo "Created a local configuration file"
fi 

if [ "$1" = "current_config" ]; then 
    python -c "import json; c = json.load(open('$local_file_path')); print('===== SIR OTIS CONFIG =====\n'+  json.dumps(c, indent=4));"
fi

if [ "$1" = "init" ]; then 
    command="python -c 'import sir_otis; sir_otis.init_sir_otis(\"$local_file_path\")'"
    eval $command
fi 

if [ "$1" = "build_sub" ]; then 
    current_contents="$2"
    command="python -c 'import sir_otis; sir_otis.build_sub(\"$local_file_path\", current_contents = \"$current_contents\")'"
    eval $command
fi

if [ "$1" = "confirm_node" ]; then 
    command="python -c 'import sir_otis; sir_otis.section_struct_to_base_contents(\"$local_file_path\")'"
    eval $command
fi
 
if [ "$1" = "expand" ]; then 

command="python -c 'import sir_otis; sir_otis.node_expansion_colab(\"$local_file_path\")'"
eval $command
fi 




if [ "$1" = "compile" ]; then 
    command="python -c 'import sir_otis; sir_otis.compile(\"$local_file_path\")'"
    eval $command
fi 

if [ "$1" = "s2" ]; then 
    command="python -c 'import sir_otis; sir_otis.structure_to_graph(\"$local_file_path\")'"
    eval $command
fi 
 

if [ "$1" = "hls" ]; then 
    base_knowledge_path=None
    while [ $# -gt 1 ]; do 
        case $1 in 
            --k) 
                base_knowledge_path="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done
    command="python -c 'import sir_otis; sir_otis.high_level_struct(\"$local_file_path\", base_knowledge_path=\"$base_knowledge_path\")'"
    # command="python -c 'import sir_otis; sir_otis.high_level_struct(\"$local_file_path\")'"
    eval $command
fi 

if [ "$1" = "tmp_save" ]; then 
    command="python -c 'import sir_otis; sir_otis.tmp_save(\"$local_file_path\")'"
    eval $command
fi 
if [ "$1" = "tmp_load" ]; then 
    command="python -c 'import sir_otis; sir_otis.tmp_load(\"$local_file_path\")'"
    eval $command
fi 


# if [ "$1" = "regen_graph" ]; then 

#     base_contents_path=None
#     structure_file=None
#     interactive_graph_path=None

#     while [ $# -gt 1 ]; do 
#         case $1 in 
#             --d) 
#                 base_contents_path="$2"
#                 shift 2
#                 ;;
#             --s) 
#                 structure_file="$2"
#                 shift 2
#                 ;;
#             --g) 
#                 interactive_graph_path="$2"
#                 shift 2
#                 ;;
#             *) 
#                 shift 1
#                 ;;
#         esac 
#     done

#     command=$(make_command "regen_graph" $local_file_path $base_contents_path $structure_file $interactive_graph_path)

#     eval $command
# fi 

# if [ "$1" = "merge" ]; then 

#     base_contents_path=None
#     structure_file=None
#     interactive_graph_path=None

#     while [ $# -gt 1 ]; do 
#         case $1 in 
#             --d) 
#                 base_contents_path="$2"
#                 shift 2
#                 ;;
#             --s) 
#                 structure_file="$2"
#                 shift 2
#                 ;;
#             --g) 
#                 interactive_graph_path="$2"
#                 shift 2
#                 ;;
#             *) 
#                 shift 1
#                 ;;
#         esac 
#     done

#     command=$(make_command "merge" $local_file_path $base_contents_path $structure_file $interactive_graph_path)

#     eval $command
# fi 

# if [ "$1" = "remove" ]; then 
#     command="python -c 'import otis; otis.delete_hash(\"$local_file_path\")'"
#     eval $command
# fi