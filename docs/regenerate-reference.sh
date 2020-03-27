cd graphkb;
mkdir -p ../docs/reference/
pydocmd simple graphkb++ > ../docs/reference/index.md;
for x in *.py;
do
    x=${x/.py/};
    if [ "$x" !=  "__init__" ];
    then
        echo $x;
        pydocmd simple graphkb.$x++ > ../docs/reference/$x.md;
    fi;
done;
cd ..

for x in docs/reference/*.md;
do
    echo "reformat google doc-strings for markdown: $x"
    sed -i 's/Args:/**Args:**\n/g' $x;
    sed -i 's/Returns:/**Returns:**\n/g' $x;
    sed -i 's/Raises:/**Raises:**\n/g' $x;
done
mkdocs build