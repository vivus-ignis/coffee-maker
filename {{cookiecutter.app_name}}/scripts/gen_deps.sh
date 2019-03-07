#!/bin/bash -e

collect_code_paths() {
    local in_file; in_file="$1"
    
    awk '/(Code|CodeUri):/ {print $2}' "$in_file" \
        | sed 's,\.\./,,g; s,target/lambda/,,g; s,.\+,target/& &/\*.py,g' \
        | xargs
}

# default yaml output of 'cloudformation package'
# does not pass yamllint checks, so we produce json
# first and convert it with cfn-flip
if [ "x${DEPLOYMENT_BUCKET}" != "x" ]; then
cat <<'EOF' > work/target_recompile_lambda.fragment 
$(PREPROCESSOR) $< | sed '/^$$/d' > $@
$(AWSCLI) --region=eu-central-1 cloudformation package \
  --template-file $@ \
  --output-template-file $@.packaged \
  --s3-bucket $(DEPLOYMENT_BUCKET) \
  --s3-prefix cloudformation \
  --use-json \
  --force-upload
cfn-flip -y $@.packaged $@
EOF
else
    cat <<'EOF' > work/target_recompile_lambda.fragment 
$(PREPROCESSOR) $< | sed '/^$$/d' > $@
EOF
fi

cat <<'EOF' > work/target_recompile.fragment 
$(PREPROCESSOR) $< | sed '/^$$/d' > $@
EOF


sed 's,.*,\t&,g' work/target_recompile.fragment > work/target_recompile.fragment_makefile_ready
mv work/target_recompile.fragment_makefile_ready work/target_recompile.fragment 

sed 's,.*,\t&,g' work/target_recompile_lambda.fragment > work/target_recompile_lambda.fragment_makefile_ready
mv work/target_recompile_lambda.fragment_makefile_ready work/target_recompile_lambda.fragment 


for f in templates/*.yaml; do
    lambda_deps=$(collect_code_paths "$f")

    if [ "x${lambda_deps}" != "x" ]; then
        cpp -traditional-cpp "$f" -MM -MT "target/$f" \
            | sed "s,[^\]$,& ${lambda_deps},g"

        for file_path in $lambda_deps; do
            if [ $(echo "$file_path" | grep 'target/') ]; then
                file_path_source=$(echo $file_path | sed 's,target/,,')
                echo -e "\tcp -r ${file_path_source}/* ${file_path}/"
                echo "%RECOMPILE_LAMBDA%"
            fi
        done
    else
        cpp -traditional-cpp "$f" -MM -MT "target/$f" \
            | sed "s,[^\]$,& ${lambda_deps}\n%RECOMPILE%,g"
    fi
done > Makefile.deps.bare

while IFS= read -r line ; do
    case $line in
        %RECOMPILE_LAMBDA%) cat work/target_recompile_lambda.fragment ;;
        %RECOMPILE%) cat work/target_recompile.fragment ;;
        *) echo "$line" ;;
    esac
done < Makefile.deps.bare > Makefile.deps
rm Makefile.deps.bare
