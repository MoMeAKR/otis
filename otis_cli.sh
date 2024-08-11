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

    command="python -c 'import otis; otis.$func_to_call(\"$local_fp\""
    
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


local_file_path=$(dirname $0)/otis_config.json

if [ "$1" = "reset" ]; then 
    rm $local_file_path
    echo "Removed the local configuration file"
fi
if [ ! -e $local_file_path ]; then 
    python -c "import otis; otis.init_config_file('$local_file_path')"
    echo "Created a local configuration file"
fi 

if [ "$1" = "current_config" ]; then 
    python -c "import json; c = json.load(open('$local_file_path')); print('===== OTIS CONFIG =====\n'+  json.dumps(c, indent=4));"
fi

if [ "$1" = "build" ]; then 
      
    base_contents_path=None
    structure_file=None
    interactive_graph_path=None

    while [ $# -gt 1 ]; do 
        case $1 in 
            --d) 
                base_contents_path="$2"
                shift 2
                ;;
            --s) 
                structure_file="$2"
                shift 2
                ;;
            --g) 
                interactive_graph_path="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done

    command=$(make_command "initial_build" $local_file_path $base_contents_path $structure_file $interactive_graph_path)

    eval $command
fi 

