Search.setIndex({docnames:["api","api/dmriprep.config","api/dmriprep.interfaces","api/dmriprep.interfaces.images","api/dmriprep.interfaces.reports","api/dmriprep.interfaces.vectors","api/dmriprep.utils","api/dmriprep.utils.bids","api/dmriprep.utils.images","api/dmriprep.utils.misc","api/dmriprep.utils.vectors","api/dmriprep.workflows","api/dmriprep.workflows.base","api/dmriprep.workflows.dwi","api/dmriprep.workflows.dwi.base","api/dmriprep.workflows.dwi.eddy","api/dmriprep.workflows.dwi.outputs","api/dmriprep.workflows.dwi.util","changes","index","installation","links","roadmap","usage"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":1,"sphinx.domains.index":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,sphinx:56},filenames:["api.rst","api/dmriprep.config.rst","api/dmriprep.interfaces.rst","api/dmriprep.interfaces.images.rst","api/dmriprep.interfaces.reports.rst","api/dmriprep.interfaces.vectors.rst","api/dmriprep.utils.rst","api/dmriprep.utils.bids.rst","api/dmriprep.utils.images.rst","api/dmriprep.utils.misc.rst","api/dmriprep.utils.vectors.rst","api/dmriprep.workflows.rst","api/dmriprep.workflows.base.rst","api/dmriprep.workflows.dwi.rst","api/dmriprep.workflows.dwi.base.rst","api/dmriprep.workflows.dwi.eddy.rst","api/dmriprep.workflows.dwi.outputs.rst","api/dmriprep.workflows.dwi.util.rst","changes.rst","index.rst","installation.rst","links.rst","roadmap.rst","usage.rst"],objects:{"dmriprep.config":{dumps:[1,1,1,""],environment:[1,2,1,""],execution:[1,2,1,""],from_dict:[1,1,1,""],get:[1,1,1,""],init_spaces:[1,1,1,""],load:[1,1,1,""],loggers:[1,2,1,""],nipype:[1,2,1,""],redirect_warnings:[1,1,1,""],to_filename:[1,1,1,""],workflow:[1,2,1,""]},"dmriprep.config.environment":{cpu_count:[1,3,1,""],exec_docker_version:[1,3,1,""],exec_env:[1,3,1,""],free_mem:[1,3,1,""],nipype_version:[1,3,1,""],overcommit_limit:[1,3,1,""],overcommit_policy:[1,3,1,""],templateflow_version:[1,3,1,""],version:[1,3,1,""]},"dmriprep.config.execution":{anat_derivatives:[1,3,1,""],bids_description_hash:[1,3,1,""],bids_dir:[1,3,1,""],bids_filters:[1,3,1,""],boilerplate_only:[1,3,1,""],debug:[1,3,1,""],fs_license_file:[1,3,1,""],fs_subjects_dir:[1,3,1,""],init:[1,4,1,""],layout:[1,3,1,""],log_dir:[1,3,1,""],log_level:[1,3,1,""],low_mem:[1,3,1,""],md_only_boilerplate:[1,3,1,""],notrack:[1,3,1,""],output_dir:[1,3,1,""],output_spaces:[1,3,1,""],participant_label:[1,3,1,""],reports_only:[1,3,1,""],run_uuid:[1,3,1,""],templateflow_home:[1,3,1,""],work_dir:[1,3,1,""],write_graph:[1,3,1,""]},"dmriprep.config.loggers":{"default":[1,3,1,""],"interface":[1,3,1,""],cli:[1,3,1,""],init:[1,4,1,""],utils:[1,3,1,""],workflow:[1,3,1,""]},"dmriprep.config.nipype":{crashfile_format:[1,3,1,""],get_linked_libs:[1,3,1,""],get_plugin:[1,4,1,""],init:[1,4,1,""],memory_gb:[1,3,1,""],nprocs:[1,3,1,""],omp_nthreads:[1,3,1,""],parameterize_dirs:[1,3,1,""],plugin:[1,3,1,""],plugin_args:[1,3,1,""],resource_monitor:[1,3,1,""],stop_on_first_crash:[1,3,1,""]},"dmriprep.config.workflow":{anat_only:[1,3,1,""],dwi2t1w_init:[1,3,1,""],fmap_bspline:[1,3,1,""],fmap_demean:[1,3,1,""],force_syn:[1,3,1,""],hires:[1,3,1,""],ignore:[1,3,1,""],longitudinal:[1,3,1,""],run_reconall:[1,3,1,""],skull_strip_fixed_seed:[1,3,1,""],skull_strip_template:[1,3,1,""],spaces:[1,3,1,""],use_syn:[1,3,1,""]},"dmriprep.interfaces":{BIDSDataGrabber:[2,2,1,""],DerivativesDataSink:[2,2,1,""],images:[3,0,0,"-"],reports:[4,0,0,"-"],vectors:[5,0,0,"-"]},"dmriprep.interfaces.DerivativesDataSink":{out_path_base:[2,3,1,""]},"dmriprep.interfaces.images":{ExtractB0:[3,2,1,""],RescaleB0:[3,2,1,""]},"dmriprep.interfaces.reports":{AboutSummary:[4,2,1,""],SubjectSummary:[4,2,1,""],SummaryInterface:[4,2,1,""]},"dmriprep.interfaces.vectors":{CheckGradientTable:[5,2,1,""]},"dmriprep.utils":{bids:[7,0,0,"-"],images:[8,0,0,"-"],misc:[9,0,0,"-"],vectors:[10,0,0,"-"]},"dmriprep.utils.bids":{collect_data:[7,1,1,""],validate_input_dir:[7,1,1,""],write_derivative_description:[7,1,1,""]},"dmriprep.utils.images":{extract_b0:[8,1,1,""],median:[8,1,1,""],rescale_b0:[8,1,1,""]},"dmriprep.utils.misc":{check_deps:[9,1,1,""],sub_prefix:[9,1,1,""]},"dmriprep.utils.vectors":{DiffusionGradientTable:[10,2,1,""],b0mask_from_data:[10,1,1,""],bvecs2ras:[10,1,1,""],calculate_pole:[10,1,1,""],normalize_gradients:[10,1,1,""],rasb_dwi_length_check:[10,1,1,""]},"dmriprep.utils.vectors.DiffusionGradientTable":{affine:[10,4,1,""],b0mask:[10,4,1,""],bvals:[10,4,1,""],bvecs:[10,4,1,""],generate_rasb:[10,4,1,""],generate_vecval:[10,4,1,""],gradients:[10,4,1,""],normalize:[10,4,1,""],normalized:[10,4,1,""],pole:[10,4,1,""],reorient_rasb:[10,4,1,""],to_filename:[10,4,1,""]},"dmriprep.workflows":{base:[12,0,0,"-"],dwi:[13,0,0,"-"]},"dmriprep.workflows.base":{init_dmriprep_wf:[12,1,1,""],init_single_subject_wf:[12,1,1,""]},"dmriprep.workflows.dwi":{base:[14,0,0,"-"],eddy:[15,0,0,"-"],outputs:[16,0,0,"-"],util:[17,0,0,"-"]},"dmriprep.workflows.dwi.base":{init_dwi_preproc_wf:[14,1,1,""]},"dmriprep.workflows.dwi.eddy":{gen_eddy_textfiles:[15,1,1,""],init_eddy_wf:[15,1,1,""]},"dmriprep.workflows.dwi.outputs":{init_reportlets_wf:[16,1,1,""]},"dmriprep.workflows.dwi.util":{init_dwi_reference_wf:[17,1,1,""],init_enhance_and_skullstrip_dwi_wf:[17,1,1,""]},dmriprep:{config:[1,0,0,"-"],interfaces:[2,0,0,"-"],utils:[6,0,0,"-"],workflows:[11,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","function","Python function"],"2":["py","class","Python class"],"3":["py","attribute","Python attribute"],"4":["py","method","Python method"]},objtypes:{"0":"py:module","1":"py:function","2":"py:class","3":"py:attribute","4":"py:method"},terms:{"02deb54a823f":1,"0rc0":[1,23],"121754_aa0b4fa9":1,"153141_be60c69":1,"1a0":19,"27121_a22e51b47c544980bad594d5e0bb2d04":10,"3bed":1,"3dautomask":17,"3dshore":22,"3dunif":17,"409b":1,"48c48a4b53bb":1,"4a11":1,"6b60":1,"6mm":17,"abstract":22,"boolean":[2,5],"break":18,"case":[22,23],"class":[0,1,2,3,4,5,10],"default":[1,2,5,15,17,22,23],"export":1,"final":[17,22],"float":[3,5,10],"function":[0,1,2,18,20,22],"import":[1,23],"int":[10,17],"long":[18,19],"new":[1,19,20],"return":10,"static":10,"switch":1,"true":[1,2,5,7,10],"try":20,ARS:10,Added:18,Adding:18,B0s:3,For:[19,20,23],LAS:10,LPS:10,NOT:23,One:[3,14],PRs:22,RAS:[10,14],The:[1,2,10,14,15,17,18,19,20,22],Then:[17,22],There:20,These:20,Use:[18,23],_config:1,_svgutils_:18,a494:1,abl:23,about:[12,18,22],aboutsummari:4,abov:[14,20,22],absenc:1,accept:22,access:[1,23],accord:18,acquisit:[10,15,19],across:[1,8,19,23],action:[1,18],adam:18,adapt:[17,19],add:[1,18],addict:18,addit:[20,23],address:[18,19,22],adher:[18,19,20],adopt:18,advanc:19,af7d:1,affili:18,affin:[10,17],afni:[17,20],afq:18,after:[1,17,18,20],aggreg:23,agnost:19,ahead:[20,22],aka:18,algorithm:[17,22],all:[1,3,10,12,18,19,20,22,23],allclos:5,alloc:1,allow:[1,18,20],allowed_ent:2,alpha:22,also:[18,19,20,22],altern:[1,20,23],although:23,alwai:22,amazonaw:10,ambiti:20,amd64:20,amount:18,amplitud:10,analysi:[19,22],analysis_level:[20,23],analyt:[1,19],anat:23,anat_deriv:1,anat_onli:1,anatom:[1,12,18,23],ani:[1,2,12,19,23],anisha:18,anoth:23,answer:19,ant:[17,19,20],antsbrainextract:23,anyon:18,api:[18,19],app:[20,23],appear:20,appli:17,applic:[17,19],approach:[20,22],appropri:22,april:19,arg:[1,2],argument:[1,19,20],ariel:[18,22],around:22,arrai:10,artifact:22,ask:19,aspect:23,assess:23,assum:23,attempt:[18,23],austin:18,autom:[1,20],automat:[19,22],avail:[1,17,19,20,23],averag:[3,8,10,22],b07ee615a588acf67967d70f5b2402ffbe477b99a316433fa7fdaff4f9dad5c1:1,b0_ix:[3,5,8,17],b0_threshold:[5,10],b0mask:10,b0mask_from_data:10,b0s:[3,17],b_0:22,b_1:22,b_scale:[5,10],back:18,bare:20,base:[0,1,2,3,4,5,10,11,13,19,20,22],base_directori:2,bash:20,basi:1,basic:19,basqu:18,batteri:[16,18],bbregist:18,bcbl:18,becom:19,bed:22,been:10,befor:[14,19],begin:19,behavior:18,being:14,below:[10,18],benchmark:22,best:19,bet:17,better:19,bia:[17,22],bias_corrected_fil:17,bid:[0,1,2,6,14,19,20],bids_description_hash:1,bids_dir:[1,7,23],bids_filt:1,bids_root:23,bids_valid:7,bidsdatagrabb:2,bidslayout:1,big:18,binari:[14,20],blob:23,board:19,boilerpl:[1,18,23],boilerplate_onli:[1,23],bold:2,bool:14,both:22,bound:23,brain:[1,17,18,19],brainmask:18,branch:18,breed:19,bring:18,broken:18,brought:22,bspline:23,bugfix:[18,22],build:[1,14,17,18,19,20],build_workflow:1,built:1,bval:[5,10],bvec:[5,10],bvec_norm_epsilon:[5,10],bvecs2ra:10,c3d:20,cach:1,calcul:[10,17,22,23],calculate_pol:10,call:[1,10,23],can:[1,18,19,20,22,23],candid:22,capabl:[18,20],carpet:22,categori:1,caus:22,center:[18,23],centr:18,chacon:19,challeng:19,chang:[1,18,19],changelog:18,channel:22,chapter:19,charact:1,chdir:[3,5],check:[5,10,18,20,23],check_dep:9,check_hdr:2,checkgradientt:5,checkout:20,checkpoint:1,checksum:1,choic:23,chose:20,cieslak:18,circleci:18,citat:[18,23],citi:23,classmethod:1,clean:[19,23],cleanenv:23,clear:23,cli:[1,23],client:[1,20],cloud:19,code:[1,12,14,17,18,19],coeffici:14,coerc:2,cognit:18,cohort:23,collat:22,collect:[1,12],collect_data:7,colon:23,com:[10,20,23],come:20,command:[1,4,18,19,20],commerci:19,commit:18,common:23,commun:22,compar:20,comparison:22,compat:14,complet:23,complex:[19,22],compliant:[1,23],compon:22,compos:[10,20,22],comprehend:12,compress:2,comput:[1,23],concern:19,concurr:23,condens:22,conduc:22,conduct:19,config:[0,18,19,23],config_fil:1,configur:[0,19,20],conform:22,confound:22,connect:18,consid:10,consist:1,consumpt:1,contact:[20,22],contain:[1,2,4,19,23],container_command_and_opt:20,container_imag:20,content:[18,23],continu:[1,18,22],contrast:17,contribut:[18,19],contributor:[18,19,22],conveni:1,convers:[1,10,22],convert:[1,10],coordin:[10,14],copi:1,core:[2,3,4,5],coregist:23,coregistr:1,correct:[5,14,15,17,19,22],correctli:[18,20],correspond:[1,10,23],could:22,count:18,countri:23,cover:[10,22],cpu:[1,23],cpu_count:1,crash:23,crashfil:1,crashfile_format:1,crawl:1,creat:[1,12,15,19,20],crucial:23,current:[1,15,19,20,22],custom:[2,17,18,23],cycl:22,daemon:20,data:[1,2,10,17,18,19,22,23],data_dir:[3,5],data_dtyp:2,datalad:18,dataset:[1,8,10,14,17,18,19,22,23],dataset_descript:1,datasink:[2,16],datatyp:2,deadlin:22,deal:3,debian:20,debug:[1,15,23],dec:22,decai:3,decemb:19,decid:22,defin:23,definit:23,delet:18,delimit:23,demean:23,dep:18,depart:18,depend:[9,18,19,23],deploi:[18,20],deploy:18,dept:18,derek:[18,22],deriv:[1,2,12,16,18,19,23],deriv_dir:7,derivatives_path:20,derivativesdatasink:[2,18],describ:[18,23],descript:[1,20],design:[1,19,22,23],detail:23,determin:22,develop:[18,19,23],dicki:18,dict:1,dictionari:[1,2],diffus:[10,12,14,15,18,19,22,23],diffusiongradientt:[10,18],dilat:17,dimens:8,dir:23,direct:12,directori:[1,2,4,23],disabl:23,disk:[1,23],dismiss_ent:2,displac:22,distort:[1,14,15,19,22],distribut:17,dmri:[14,19,23],dmriprep:[0,20,22,23],dmriprep_named_opt:20,doc:[18,20],docker:[1,18,19,23],dockerfil:[18,20],dockerout:23,document:[18,19,20,22],doe:[1,23],don:23,done:23,draft:22,drift:3,driven:[10,18],drop:[18,20],ds001771:18,dtype:[2,18],dump:1,dwi2t1w:23,dwi2t1w_init:1,dwi:[0,1,2,3,4,5,8,10,11,12,18,22,23],dwi_fil:[5,10,14,15,17],dwi_mask:[3,14,17],dwi_refer:14,dwi_reference_wf:17,each:[1,12,17,19,23],earli:1,easi:19,easili:[1,19],eddi:[0,11,13,18,19,22,23],eddy_openmp:15,eddy_wf:15,edu:23,effect:23,effort:22,either:[1,23],element:17,els:22,email:19,enabl:[1,22,23],encod:10,encompass:19,end:19,engin:[1,20],enh:18,enhanc:17,enhance_and_skullstrip_dwi_wf:17,enlist:1,ensembl:22,ensur:[5,19,23],entiti:[2,12,23],environ:[1,18,19,23],equip:19,equival:22,erin:18,error:[1,18,23],escienc:18,esteban:18,estim:[1,3,10,15,18,22],etc:[1,19],evalu:[10,22],even:23,event:[22,23],everi:1,exact:23,exampl:[1,3,5,9,10,15,19,20,23],exclus:[5,22],exec_docker_vers:1,exec_env:[1,7],execut:[1,12,18,19,20,22],exercis:18,exist:[1,2,3,4,5,23],exit:23,expect:22,experi:22,experiment:23,explain:19,explicit:18,explor:22,extern:19,extra:20,extract:[1,2,3,8,17],extract_b0:[3,8],extractb0:3,eye:10,fact:[18,23],factor:3,fair:18,fals:[1,2,10,14,15,16],familiar:19,fast:[1,18],favour:18,featur:18,februari:19,feel:19,field:[1,17,23],fieldmap:[1,2,14,18,19,22],figure1:18,file:[1,2,3,4,5,10,14,15,17,18,20,23],filenam:[1,10],filesystem:1,filetyp:10,filter:[1,19],find:19,finish:22,first:[1,18,20,22,23],fit:[19,23],fix:[1,2,18,23],fixed_hdr:2,flag:[1,18,22,23],flair:2,flake8:18,flat:1,flexibl:18,flow:19,flowchart:18,fmap:[2,14,23],fmap_bsplin:1,fmap_coeff:14,fmap_demean:1,fmap_id:14,fmap_mask:14,fmap_ref:14,fmriprep:[18,22,23],focu:22,folder:[1,12,23],follow:[18,20,22,23],forc:23,force_syn:1,forkserv:1,form:[5,23],format:[1,19],forward:18,found:[1,18,20,23],frame:10,framewis:22,framework:20,free:[1,19,20,23],free_mem:1,freesurf:[1,4,12,18,19,20],freesurfer_hom:23,from:[1,2,3,8,17,18,19,20,22,23],from_dict:1,from_fil:[3,4,5],front:18,fs_licens:23,fs_license_fil:1,fs_subjects_dir:1,fsl:[15,17,18,20,22],full:[1,10,12,18],full_spher:5,fullds005:23,fund:23,further:[22,23],futur:[19,22,23],garikoitz:18,gdf07e84f:[1,23],gen_eddy_textfil:15,gener:[1,4,15,17,18,19,20,22,23],generate_rasb:10,generate_vecv:10,get:[1,10,20,23],get_linked_lib:1,get_plugin:1,gibb:22,gihub:18,git:19,github:[18,19,23],given:[1,10],going:18,googl:[1,19],gradient:[5,10,14,22],gradients_rasb:14,graph:[1,12,14,17,23],grid:23,guid:22,guidelin:[18,19,22],habitu:20,had:17,half:10,halford:18,hand:20,handl:[5,7,8,19,20],happen:1,happi:19,hard:1,harvard:23,has:[1,9,19,20],has_fieldmap:14,hash:1,have:[10,20,22,23],head:[15,19,22],header:[1,2,23],health:18,hello:20,help:[19,23],hemispher:10,heurist:1,high:19,highli:23,hire:[1,23],histogram:17,hoc:19,holder:22,home:[1,23],honor:18,hospit:18,host:[20,23],hous:22,how:20,hpc:19,html:[1,4,10,17,23],http:[10,20,23],hub:20,idea:[19,20],identif:[18,22],identifi:[1,20,22,23],idiosyncrasi:19,ignor:[1,23],imag:[0,2,4,6,10,15,17,18,20,22,23],implement:[1,2,18,19,22],impli:23,improv:[18,20,23],imput:22,in_bval:[5,14],in_bvec:[5,14],in_fil:[2,3,8,15,17],in_meta:15,in_rasb:5,includ:[18,19,22,23],inconsist:18,increas:23,index:[3,15,17],indic:[17,23],individu:[17,18],infer:19,info:1,inform:[0,1,12,23],infrastructur:[18,20],inhomogen:22,init:[1,23],init_dmriprep_wf:12,init_dwi_preproc_wf:14,init_dwi_reference_wf:[14,17],init_eddy_wf:15,init_enhance_and_skullstrip_dwi_wf:17,init_enhance_and_skullstrip_wf:17,init_reportlets_wf:[14,16],init_single_subject_wf:12,init_spac:1,initi:[1,17,18,22,23],input:[2,3,4,5,7,8,12,14,15,17,23],input_bids_path:20,instal:[1,19,23],instanc:[1,12,18],instead:[18,22],institut:18,instruct:20,integ:[3,5],integr:[18,22],intend:23,intendedfor:18,intens:[8,17],interest:22,interfac:[1,18,19,20],intermedi:[1,23],interpret:[19,20],intersect:17,intervent:19,introduc:19,inu:17,inventori:19,investig:22,invit:22,iowa:18,isbi:22,ismrm:22,issu:[1,18,19,22],item:[2,3,4,5,18],iter:[1,17,18],its:17,jame:18,januari:19,jell:18,join:1,joseph:18,json:[1,23],just:10,keep:[1,22,23],kei:[2,23],kent:18,kernel:[1,20],keshavan:18,keyword:23,known:20,krembil:18,kwarg:2,label:[12,14,23],languag:18,laptop:19,larg:[18,19],last:[8,10],latest:[17,18,22,23],latex:[1,23],lausann:18,layout:[1,23],learn:19,least:23,left:[1,2,22],leftov:18,length:10,lerma:18,less:[1,22],level:[1,20,23],librari:[1,19],licens:[1,18,19,20],lie:10,lightweight:20,like:[1,19,22],limit:[1,19,20,23],line:[1,19,20,22],linear:22,lineno:1,link:[1,18],lint:18,linux:[1,20],list:[1,2,3,4,5,10,12,17,19,20,23],load:[1,18],loadtxt:5,local:[18,23],locat:[10,16,23],log:[0,19,23],log_dir:1,log_level:1,logger:1,logitudin:1,longitudin:[1,23],look:[1,19],loos:17,low:[10,23],low_mem:1,machin:20,magic:1,mai:[12,17,18,19,23],maint:18,maintain:[1,19],mainten:18,make:[9,10,19,20,22],makefil:18,manag:1,mandatori:[2,3,5],mani:20,mansour:18,manual:[19,23],manuscript:18,map:[18,19],march:19,mark:18,markdown:1,mask:[3,10,14,17,22,23],mask_fil:[3,8,10,17],master:23,mathemat:17,matter:22,mattermost:[19,22],matthew:18,maximum:[17,23],maxtasksperchild:1,md_only_boilerpl:1,mean:[1,10,23],measur:22,median:[8,17,23],medicin:18,meet:22,mem:23,mem_gb:17,mem_mb:23,memori:[1,23],memory_gb:[1,23],mental:18,messag:[1,20],meta_dict:2,metadata:2,metal:20,method:[0,20,23],methodolog:17,mgh:23,mgr:1,michael:18,migrat:18,mileston:[18,19],millimet:23,minim:[1,18],minor:18,misc:[0,6],miscellan:9,modal:14,mode:[1,18],model:[19,22],modifi:[20,23],modul:[0,1,2,6,11,13,18],monitor:[1,23],month:22,monthli:22,more:[18,19,20,22],morpholog:17,most:[10,18,20,22],mostli:22,motion:[15,19,22],move:18,mri:[12,14,19],multi:20,multipl:22,multiproc:1,multiprocess:1,multithread:1,music:22,must:[1,10,20,23],mutual:5,n4biasfieldcorrect:17,n_cpu:23,name:[2,15,16,17,18,19,20],named_opt:20,ndarrai:10,necessari:20,need:[1,12],neurodock:20,neurohackademi:18,neuroimag:[19,20],neuroinformat:18,neurosci:18,neuroscientist:19,neurostar:19,newer:19,newrasb:5,next:20,nice:19,nifti:[1,2,14,15,17],nii:[3,5,15],niprep:[18,19,20,23],nipyp:[1,2,3,4,5,18,19,20,23],nipype_vers:1,niworkflow:[2,7,17,18],nlmean:22,nmr:23,node:[1,17,23],nois:22,noisi:22,non:[1,4,10,22,23],none:[1,2,3,4,5,8,10],nonstandard:1,norm:10,norm_val:10,norm_vec:10,normal:[10,14,23],normalize_gradi:10,note:[22,23],notebook:22,notrack:[1,23],notrecommend:23,novemb:19,now:23,nproc:[1,18,23],nstd_space:4,nthread:23,number:[1,10,12,17,22,23],numer:19,numpi:[2,10],oasis30:1,object:[1,2,3,4,5,10],obtain:[20,23],occurr:23,octob:[19,22],oesteban:1,off:22,offici:22,oldrasb:5,omp:23,omp_nthread:[1,17,23],on_fail:18,onc:20,one:[12,14,17,23],ones:10,ongo:22,onli:[1,22,23],onlin:23,oper:[1,10,20,23],oppos:12,opt:[1,23],option:[1,2,4,5,18,19,20,22],orchestr:14,order:22,org:[19,23],organ:12,orient:[10,23],origin:23,oscar:18,osf:18,other:[0,17,18,19,20,22],otherwis:1,othewis:10,our:[18,19,20,22],out:[1,18,20,23],out_acqparam:15,out_b0:3,out_bval:5,out_bvec:5,out_dict:2,out_eddi:15,out_fil:[2,3],out_index:15,out_meta:2,out_path:8,out_path_bas:2,out_rasb:5,out_ref:3,out_report:[4,17],outcom:[22,23],outlier:22,output:[0,1,2,3,4,5,11,13,14,15,17,18,19,20,23],output_dir:[1,16,23],output_spac:[1,23],over:[1,3,18],overal:19,overcommit:1,overcommit_limit:1,overcommit_polici:1,overdu:18,overhaul:18,packag:[0,18,19,20],page:18,pair:10,pandoc:23,parallel:[1,17],paramet:[1,10,12,14,15,17,23],parameter:1,parameterize_dir:1,part:[22,23],particip:[1,23],participant_id:1,participant_label:[1,7,23],particular:[1,19],pass:[1,23],patch2self:22,patch:2,path:[1,2,10,14,15,18,20,23],pathlik:[2,3,4,5,12,14],pca:22,pdf:[12,14,17],pennsylvania:18,per:23,perelman:18,perform:[12,17,19],phase:22,phaseencodingdirect:15,philosophi:[19,22],pickl:1,pin:18,pip:20,pipelin:[12,18,19],pisner:18,place:22,plan:[1,19],platform:1,pleas:[18,19,20,22,23],plot:22,plugin:[1,18,23],plugin_arg:1,png:[12,14,17],point:[10,23],poldrack:18,pole:[5,10],polici:1,pop:19,popul:12,popular:20,popylar:[18,23],port:[18,22],posit:19,posix:1,posixpath:1,possibl:[1,23],pre_mask:17,preambl:20,prefer:22,prefix:[9,23],premier:22,prep:18,prepar:[12,18,19,23],preprocess:[1,12,14,18,19],present:[9,22],pretti:22,previou:[18,23],price:20,princip:23,principl:18,pro:19,probabl:20,process:[1,12,14,17,18,19,22,23],produc:20,program:[18,19,23],project:[1,19],promin:22,propag:2,properti:10,propos:22,protocol:22,provid:[19,22,23],psychiatri:18,psycholog:18,pub:10,pull:20,pybid:23,pypi:20,python:[1,18,19],qsiprep:22,qualiti:[19,23],queri:19,question:19,radiolog:18,rais:18,raise_error:10,raise_inconsist:10,raise_insuffici:1,ram:1,random:23,rapid:19,rasb:[10,14],rasb_dwi_length_check:10,rasb_fil:10,raw:10,raw_ref_imag:17,reach:22,read:[1,20,22],read_text:15,readi:[20,22],readm:18,real:23,realli:10,reason:[20,23],recent:10,recommend:[19,23],recon:[1,12,23],reconal:23,reconstruct:[1,23],record:23,redirect:1,redirect_warn:1,reduc:23,ref_imag:17,ref_image_brain:17,refactor:18,refer:[1,10,14,17,18,23],regard:[1,22],regardless:12,regist:[1,14,17,23],registr:[18,19],registri:18,regular:1,rel:[10,20],relat:19,releas:[18,22],remov:[1,17,18,23],reorgan:18,reorient:[10,18],reorient_rasb:10,replac:[1,7,22],replic:23,repo:22,report:[0,1,2,12,16,18,22,23],reportlet:[1,4,16,17,18,23],reportlets_wf:16,reports_bug:18,reports_onli:1,repres:[1,2,3,4,5],represent:[1,18],reproduc:19,requir:[20,23],rero:22,rerun:23,res:[3,23],resampl:23,rescal:[3,8,17],rescale_b0:[3,8],rescaleb0:3,research:[19,22],resolut:23,resourc:[1,23],resource_monitor:[1,3,4,5],respons:[0,19],result:[1,10,19,23],resultinb:10,retval:1,reus:23,revis:18,richi:18,rician:22,right:16,ring:22,road:[18,19],roadmap:[18,19],robust:19,roi:2,rokem:18,roll:18,root:[1,23],rootlogg:1,rstudio:10,rtol:5,run:[1,3,5,12,14,17,18,20,22,23],run_reconal:1,run_unique_id:1,run_uuid:[1,23],runtim:[1,23],russel:18,salient:18,salim:[18,22],same:20,sampl:23,save:[2,18],sbref:[2,23],scale:14,scan:18,schedul:22,school:18,score:10,scott:19,script:18,sdc:23,sdc_report:16,sdcflow:[18,22],search:23,section:[0,19,20],secur:20,see:[1,19,20,23],seed:[1,23],segment:4,select:[1,23],send:23,sent:20,sentri:18,separ:[12,23],septemb:19,seri:[3,10,23],serv:[18,22],session:[1,12,18],set:[1,12,16,18,19,20,22,23],sever:[12,22],sfm:22,sha256:1,shape:10,share:[1,20],sharpen:17,shell:[10,22],shorelin:22,should:[1,2,20,22,23],show:[18,20,23],signal:[3,8,10,17],signal_drift:3,simpleinterfac:[2,3,4,5],simpli:23,simplic:18,singl:[1,12,17,22,23],singleton:1,singular:[19,23],skip:23,skiprow:5,skull:[1,17,23],skull_strip_fixed_se:1,skull_strip_templ:[1,23],skull_stripped_fil:17,skullstrip:18,sloppi:[1,18,23],small:18,smoke:18,smriprep:[1,18],snowbal:19,softwar:[19,20,22,23],solid:22,solut:22,some:[1,18,19,20,22,23],someth:20,somewher:19,sort:22,sourc:[2,12,14,17],source_fil:2,space:[1,4,19,23],spatial:[1,23],spatialrefer:1,specif:[0,18,19,22],specifi:[20,23],speed:23,sphere:[10,17],spline:[1,23],sprint:[18,22],squar:[10,23],stabl:22,stage:23,stake:22,standard:[1,4,10,17,19,23],stanford:18,start:[1,18,19,20,22],state:19,statist:23,std_space:4,step:[1,17,18,19,20,22],still:19,stop:[1,23],stop_on_first_crash:1,store:[1,2,16,23],str:[1,2,3,5,10,12,15,17],stream:20,string:[1,2,3,4,5],strip:[1,17,23],structur:[1,2,4,10,17,20,23],sty:18,sub:[1,9,12,18,23],sub_prefix:9,subid:9,subject:[1,4,9,12,23],subject_data:2,subject_id:[2,4,12],subjects_dir:[4,12],subjectsummari:4,submit:[18,19],submm:23,submodul:[0,19],suboptim:1,subpackag:[0,19],subprocess:1,successfulli:23,suffix:23,summari:4,summaryinterfac:4,support:[18,19,22],sure:[9,19,20,22],surfac:[1,19],surfer:23,suscept:[1,14,19],svg:[12,14,17,18],syn:19,system:[9,20,23],t1w:[2,4,18,22,23],t2w:[2,4],tabl:[5,10,14],tacc:20,tag:18,take:[17,19,22,23],target:[1,18,19],task:[1,18],task_id:18,tbd:19,team:22,techniqu:22,technolog:19,templat:[1,12,23],templateflow:1,templateflow_hom:1,templateflow_vers:1,temporari:[18,22,23],tenant:20,term:19,termin:20,test:[18,22,23],texa:18,text:1,thei:22,them:[17,18,22],therefor:20,thi:[1,9,10,12,17,18,19,20,22,23],thp0005:1,thp002:1,thread:[17,23],threshold:10,through:[22,23],time:[1,3,23],tip:20,tmp:1,tmpdir:[3,5],to_filenam:[1,10],tolist:10,tomatch:2,toml:1,took:20,tool:[1,3,18,19,20,23],top:23,topup:18,toronto:18,totalreadouttim:15,toward:22,traceback:10,track:[1,18,19],transform:10,transpar:19,travisci:18,treat:23,trick:[1,20],tsv:5,tupl:5,tutori:22,two:[12,20],txt:[1,23],type:10,typo:18,ubuntu:20,uncompress:[1,2],under:[1,20],uniqu:1,unit:[10,18],univers:18,unless:23,unmodifi:2,until:22,updat:[18,19,22],upon:19,upper:23,upstream:18,usa:18,usabiaga:18,usag:[0,18,19,20],use:[1,17,18,19,20,22,23],use_plugin:23,use_syn:1,used:[1,14,20,22,23],useful:1,user:[1,20,22],uses:23,using:[1,8,12,17,18,20,22,23],usr:1,util:[0,1,11,13,18,19],uuid:23,val:18,valid:[17,19,20,23],validate_input_dir:7,validation_report:17,valu:[1,2,5,10,14,17,23],valueerror:10,variabl:[1,23],variat:10,varieti:19,vec:[10,18],vector:[0,2,6,14,18],veraart:18,verbos:[1,23],veri:23,version:[1,4,7,17,18,19,20,23],via:1,video:[18,19],virtual:[1,19,20],visit:20,visual:23,volum:[3,8,10,17,22,23],voxel:22,vstack:10,vvv:23,wai:[10,20,22],want:[19,23],warn:1,washington:18,websit:18,weekli:22,weight:10,welcom:19,well:22,were:20,what:19,when:[1,18,23],whenev:1,where:[1,10,19,22,23],whether:[1,2,10,17,22,23],which:[1,2,3,4,5,10,18,19,20,22,23],white:22,who:22,whole:19,wide:1,within:[10,20,22,23],without:[19,23],work:[1,18,20,22,23],work_dir:[1,23],workdir:23,workflow:[0,1,9,18,19,20],world:[20,23],would:22,wrap:22,write:[1,10,16,18,23],write_derivative_descript:7,write_graph:1,written:[1,20],www:23,xxxxx:23,year:18,york:18,you:[19,20,22,23],your:[19,20,23],yourself:19,z_thre:10,zenodo:18,zero:10},titles:["Library API (application program interface)","dmriprep.config package","dmriprep.interfaces package","dmriprep.interfaces.images module","dmriprep.interfaces.reports module","dmriprep.interfaces.vectors module","dmriprep.utils package","dmriprep.utils.bids module","dmriprep.utils.images module","dmriprep.utils.misc module","dmriprep.utils.vectors module","dmriprep.workflows package","dmriprep.workflows.base module","dmriprep.workflows.dwi package","dmriprep.workflows.dwi.base module","dmriprep.workflows.dwi.eddy module","dmriprep.workflows.dwi.outputs module","dmriprep.workflows.dwi.util module","What\u2019s new?","dMRIPrep","Installation","&lt;no title&gt;","Development road-map","Usage"],titleterms:{"1a0":18,"long":22,"new":18,The:23,about:19,analyt:23,ant:23,api:0,applic:0,april:22,argument:23,author:18,base:[12,14,18],befor:22,bid:[7,23],cloud:20,command:23,commerci:20,config:1,configur:[1,23],contain:20,content:19,correct:23,decemb:18,depend:20,develop:22,distort:23,dmriprep:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],docker:20,dwi:[13,14,15,16,17],eddi:15,end:22,environ:20,execut:23,extern:20,februari:22,fieldmap:23,filter:23,format:23,freesurf:23,get:19,googl:23,handl:23,hpc:20,imag:[3,8],instal:20,interfac:[0,2,3,4,5],involv:19,januari:[18,22],laptop:20,librari:0,licens:23,line:23,list:18,log:1,mai:22,manual:20,map:22,march:22,misc:9,modul:[3,4,5,7,8,9,10,12,14,15,16,17],name:23,novemb:18,octob:18,option:23,other:[1,23],output:16,packag:[1,2,6,11,13],paper:18,perform:23,plan:22,posit:23,prepar:20,preprocess:23,program:0,python:20,queri:23,recommend:20,registr:23,report:4,respons:1,road:22,section:1,septemb:[18,22],seri:18,singular:20,specif:23,submodul:[2,6,11,13],subpackag:11,surfac:23,syn:23,target:22,tbd:18,technolog:20,term:22,track:23,usag:[1,23],util:[6,7,8,9,10,17],vector:[5,10],version:22,what:18,workflow:[11,12,13,14,15,16,17,23]}})