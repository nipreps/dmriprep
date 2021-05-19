Search.setIndex({docnames:["api","api/dmriprep.config","api/dmriprep.interfaces","api/dmriprep.interfaces.images","api/dmriprep.interfaces.reports","api/dmriprep.interfaces.vectors","api/dmriprep.utils","api/dmriprep.utils.bids","api/dmriprep.utils.images","api/dmriprep.utils.misc","api/dmriprep.utils.vectors","api/dmriprep.workflows","api/dmriprep.workflows.base","api/dmriprep.workflows.dwi","api/dmriprep.workflows.dwi.base","api/dmriprep.workflows.dwi.eddy","api/dmriprep.workflows.dwi.outputs","changes","index","installation","links","roadmap","usage"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":1,"sphinx.domains.index":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,sphinx:56},filenames:["api.rst","api/dmriprep.config.rst","api/dmriprep.interfaces.rst","api/dmriprep.interfaces.images.rst","api/dmriprep.interfaces.reports.rst","api/dmriprep.interfaces.vectors.rst","api/dmriprep.utils.rst","api/dmriprep.utils.bids.rst","api/dmriprep.utils.images.rst","api/dmriprep.utils.misc.rst","api/dmriprep.utils.vectors.rst","api/dmriprep.workflows.rst","api/dmriprep.workflows.base.rst","api/dmriprep.workflows.dwi.rst","api/dmriprep.workflows.dwi.base.rst","api/dmriprep.workflows.dwi.eddy.rst","api/dmriprep.workflows.dwi.outputs.rst","changes.rst","index.rst","installation.rst","links.rst","roadmap.rst","usage.rst"],objects:{"dmriprep.config":{dumps:[1,1,1,""],environment:[1,2,1,""],execution:[1,2,1,""],from_dict:[1,1,1,""],get:[1,1,1,""],init_spaces:[1,1,1,""],load:[1,1,1,""],loggers:[1,2,1,""],nipype:[1,2,1,""],redirect_warnings:[1,1,1,""],to_filename:[1,1,1,""],workflow:[1,2,1,""]},"dmriprep.config.environment":{cpu_count:[1,3,1,""],exec_docker_version:[1,3,1,""],exec_env:[1,3,1,""],free_mem:[1,3,1,""],nipype_version:[1,3,1,""],overcommit_limit:[1,3,1,""],overcommit_policy:[1,3,1,""],templateflow_version:[1,3,1,""],version:[1,3,1,""]},"dmriprep.config.execution":{anat_derivatives:[1,3,1,""],bids_description_hash:[1,3,1,""],bids_dir:[1,3,1,""],bids_filters:[1,3,1,""],boilerplate_only:[1,3,1,""],debug:[1,3,1,""],fs_license_file:[1,3,1,""],fs_subjects_dir:[1,3,1,""],init:[1,4,1,""],layout:[1,3,1,""],log_dir:[1,3,1,""],log_level:[1,3,1,""],low_mem:[1,3,1,""],md_only_boilerplate:[1,3,1,""],notrack:[1,3,1,""],output_dir:[1,3,1,""],output_spaces:[1,3,1,""],participant_label:[1,3,1,""],reports_only:[1,3,1,""],run_uuid:[1,3,1,""],templateflow_home:[1,3,1,""],work_dir:[1,3,1,""],write_graph:[1,3,1,""]},"dmriprep.config.loggers":{"default":[1,3,1,""],"interface":[1,3,1,""],cli:[1,3,1,""],init:[1,4,1,""],utils:[1,3,1,""],workflow:[1,3,1,""]},"dmriprep.config.nipype":{crashfile_format:[1,3,1,""],get_linked_libs:[1,3,1,""],get_plugin:[1,4,1,""],init:[1,4,1,""],memory_gb:[1,3,1,""],nprocs:[1,3,1,""],omp_nthreads:[1,3,1,""],parameterize_dirs:[1,3,1,""],plugin:[1,3,1,""],plugin_args:[1,3,1,""],resource_monitor:[1,3,1,""],stop_on_first_crash:[1,3,1,""]},"dmriprep.config.workflow":{anat_only:[1,3,1,""],dwi2t1w_init:[1,3,1,""],fmap_bspline:[1,3,1,""],fmap_demean:[1,3,1,""],force_syn:[1,3,1,""],hires:[1,3,1,""],ignore:[1,3,1,""],longitudinal:[1,3,1,""],run_reconall:[1,3,1,""],skull_strip_fixed_seed:[1,3,1,""],skull_strip_template:[1,3,1,""],spaces:[1,3,1,""],use_syn:[1,3,1,""]},"dmriprep.interfaces":{BIDSDataGrabber:[2,2,1,""],DerivativesDataSink:[2,2,1,""],images:[3,0,0,"-"],reports:[4,0,0,"-"],vectors:[5,0,0,"-"]},"dmriprep.interfaces.DerivativesDataSink":{out_path_base:[2,3,1,""]},"dmriprep.interfaces.images":{ExtractB0:[3,2,1,""],RescaleB0:[3,2,1,""]},"dmriprep.interfaces.reports":{AboutSummary:[4,2,1,""],SubjectSummary:[4,2,1,""],SummaryInterface:[4,2,1,""]},"dmriprep.interfaces.vectors":{CheckGradientTable:[5,2,1,""]},"dmriprep.utils":{bids:[7,0,0,"-"],images:[8,0,0,"-"],misc:[9,0,0,"-"],vectors:[10,0,0,"-"]},"dmriprep.utils.bids":{collect_data:[7,1,1,""],validate_input_dir:[7,1,1,""],write_derivative_description:[7,1,1,""]},"dmriprep.utils.images":{extract_b0:[8,1,1,""],median:[8,1,1,""],rescale_b0:[8,1,1,""]},"dmriprep.utils.misc":{check_deps:[9,1,1,""],sub_prefix:[9,1,1,""]},"dmriprep.utils.vectors":{DiffusionGradientTable:[10,2,1,""],b0mask_from_data:[10,1,1,""],bvecs2ras:[10,1,1,""],calculate_pole:[10,1,1,""],normalize_gradients:[10,1,1,""],rasb_dwi_length_check:[10,1,1,""]},"dmriprep.utils.vectors.DiffusionGradientTable":{affine:[10,4,1,""],b0mask:[10,4,1,""],bvals:[10,4,1,""],bvecs:[10,4,1,""],generate_rasb:[10,4,1,""],generate_vecval:[10,4,1,""],gradients:[10,4,1,""],normalize:[10,4,1,""],normalized:[10,4,1,""],pole:[10,4,1,""],reorient_rasb:[10,4,1,""],to_filename:[10,4,1,""]},"dmriprep.workflows":{base:[12,0,0,"-"],dwi:[13,0,0,"-"]},"dmriprep.workflows.base":{init_dmriprep_wf:[12,1,1,""],init_single_subject_wf:[12,1,1,""]},"dmriprep.workflows.dwi":{base:[14,0,0,"-"],eddy:[15,0,0,"-"],outputs:[16,0,0,"-"]},"dmriprep.workflows.dwi.base":{init_dwi_preproc_wf:[14,1,1,""]},"dmriprep.workflows.dwi.eddy":{gen_eddy_textfiles:[15,1,1,""],init_eddy_wf:[15,1,1,""]},"dmriprep.workflows.dwi.outputs":{init_dwi_derivatives_wf:[16,1,1,""],init_reportlets_wf:[16,1,1,""]},dmriprep:{config:[1,0,0,"-"],interfaces:[2,0,0,"-"],utils:[6,0,0,"-"],workflows:[11,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","function","Python function"],"2":["py","class","Python class"],"3":["py","attribute","Python attribute"],"4":["py","method","Python method"]},objtypes:{"0":"py:module","1":"py:function","2":"py:class","3":"py:attribute","4":"py:method"},terms:{"02deb54a823f":1,"053518_bc26688e":1,"121754_aa0b4fa9":1,"27121_a22e51b47c544980bad594d5e0bb2d04":10,"3dshore":21,"4a11":1,"4d9c":1,"6b60":1,"9c91":1,"abstract":21,"boolean":[2,5],"break":17,"case":[21,22],"class":[0,1,2,3,4,5,10],"default":[1,2,5,15,16,21,22],"export":1,"final":21,"float":[3,5,10],"function":[0,1,2,17,19,21],"import":[1,22],"int":10,"long":[17,18],"new":[1,18,19],"return":10,"static":10,"switch":1,"true":[1,2,5,7,10],"try":19,ARS:10,Added:17,Adding:17,B0s:3,For:[18,19,22],LAS:10,LPS:10,NOT:22,One:[3,14,16],PRs:21,RAS:[10,14],The:[1,2,10,14,15,16,17,18,19,21],Then:21,There:19,These:19,Use:[17,22],_config:1,_svgutils_:17,abl:22,about:[12,17,21],aboutsummari:4,abov:[14,19,21],absenc:1,accept:21,access:[1,22],accord:17,acquisit:[10,15,18],across:[1,8,18,22],action:[1,17],adam:17,adapt:18,add:[1,17],addict:17,addit:[19,22],address:[17,18,21],adher:[17,18,19],adopt:17,advanc:18,af7d:1,affili:17,affin:10,afni:19,afq:17,after:[1,17,19],aggreg:22,agnost:18,agre:18,ahead:[19,21],aka:17,algorithm:21,all:[1,3,10,12,17,18,19,21,22],allclos:5,alloc:1,allow:[1,17,19],allowed_ent:2,alpha:21,also:[17,18,19,21],altern:[1,19,22],although:22,alwai:21,amazonaw:10,ambiti:19,amd64:19,amount:17,amplitud:10,analysi:[18,21],analysis_level:[19,22],analyt:[1,18],anat:22,anat_deriv:1,anat_onli:1,anatom:[1,12,17,22],ani:[1,2,12,18,22],anisha:17,anoth:22,answer:18,ant:[18,19],antsbrainextract:22,anyon:17,apach:18,api:[17,18],app:[19,22],appear:19,applic:18,approach:[19,21,22],appropri:21,april:18,arg:[1,2],argument:[1,18,19],ariel:[17,21],around:21,arrai:10,artifact:21,ask:18,aspect:22,assess:22,assum:22,attempt:[17,22],austin:17,autom:[1,19],automat:[18,21],avail:[1,18,19,22],averag:[3,8,10,21],b07ee615a588acf67967d70f5b2402ffbe477b99a316433fa7fdaff4f9dad5c1:1,b0_ix:[3,5,8],b0_mask:5,b0_threshold:[5,10],b0mask:10,b0mask_from_data:10,b0s:3,b_0:21,b_1:21,b_scale:[5,10],back:17,bare:19,base:[0,1,2,3,4,5,10,11,13,18,19,21],base_directori:2,bash:19,basi:[1,18],basic:18,basqu:17,batteri:[16,17],bbregist:17,bcbl:17,becom:18,bed:21,been:10,befor:[14,18],begin:18,behavior:17,being:14,below:[10,17],benchmark:21,best:18,better:[17,18],bia:21,bid:[0,1,2,6,14,18,19],bids_description_hash:1,bids_dir:[1,7,22],bids_filt:1,bids_root:22,bids_valid:7,bidsdatagrabb:2,bidslayout:1,big:17,binari:[14,19],blob:22,board:18,boilerpl:[1,17,22],boilerplate_onli:[1,22],bold:2,bool:14,both:21,bound:22,brain:[1,16,17,18],brainmask:17,branch:17,breed:18,bring:17,broken:17,brought:21,bugfix:[17,21],build:[1,14,17,18,19],build_workflow:1,built:1,bval:[5,10],bvec:[5,10],bvec_norm_epsilon:[5,10],bvecs2ra:10,c41d1d1281f9:1,cach:1,calcul:[10,21,22],calculate_pol:10,call:[1,10,22],can:[1,17,18,19,21,22],candid:21,capabl:[17,19],carpet:21,categori:1,caus:21,center:[17,22],centr:17,chacon:18,challeng:18,chang:[1,17,18],changelog:17,channel:21,chapter:18,charact:1,chdir:[3,5],check:[5,10,17,18,19,22],check_dep:9,check_hdr:2,checkgradientt:5,checkout:19,checkpoint:1,checksum:1,choic:22,chose:19,cieslak:17,circleci:17,citat:[17,22],citi:22,classmethod:1,clean:[18,22],cleanenv:22,clear:22,cli:[1,22],client:[1,19],cloud:18,code:[1,12,14,17,18],coeffici:14,coerc:2,cognit:17,cohort:22,collat:21,collect:[1,12],collect_data:7,colon:22,com:[10,19,22],come:19,command:[1,4,17,18,19],commerci:18,commit:17,common:22,commun:[18,21],compar:19,comparison:21,compat:14,complet:22,complex:[18,21],complianc:18,compliant:[1,22],compon:21,compos:[10,19,21],comprehend:12,compress:2,comput:[1,22],concern:18,concurr:22,condens:21,condit:18,conduc:21,conduct:18,config:[0,17,18,22],config_fil:1,configur:[0,18,19],conform:21,confound:21,connect:17,consid:10,consist:1,consumpt:1,contact:[19,21],contain:[1,2,4,18,22],container_command_and_opt:19,container_imag:19,content:[17,22],continu:[1,17,21],contribut:[17,18],contributor:[17,18,21],conveni:1,convers:[1,10,21],convert:[1,10],coordin:[10,14],copi:[1,18],copyright:18,core:[2,3,4,5],coregistr:1,correct:[5,14,15,18,21],correctli:[17,19],correspond:[1,10,22],could:21,count:17,countri:22,cover:[10,21],cpu:[1,22],cpu_count:1,crash:22,crashfil:1,crashfile_format:1,crawl:1,creat:[1,12,15,18,19],criteria:18,crucial:22,current:[1,15,18,19,21],custom:[2,17,22],cycl:21,daemon:19,data:[1,2,10,17,18,21,22],data_dir:[3,5],data_dtyp:2,datalad:17,dataset:[1,8,10,14,17,18,21,22],dataset_descript:1,datasink:[2,16],datatyp:2,deadlin:21,deal:3,debian:19,debug:[1,15,22],dec:21,decai:3,decemb:18,decid:21,defin:22,definit:22,delet:17,delimit:22,dep:17,depart:17,depend:[9,17,18,22],deploi:[17,19],deploy:17,dept:17,derek:[17,21],deriv:[1,2,12,16,17,18,22],deriv_dir:7,derivatives_path:19,derivativesdatasink:[2,17],describ:[17,22],descript:[1,19],design:[1,18,21,22],detail:[18,22],determin:21,develop:[17,18,22],dicki:17,dict:1,dictionari:[1,2],diffus:[10,12,14,15,17,18,21,22],diffusiongradientt:[10,17],dimens:8,dir:22,direct:12,directori:[1,2,4,16,22],disabl:22,discourag:22,disk:[1,22],dismiss_ent:2,displac:21,distort:[1,14,15,18,21],distribut:18,dmri:[14,18,22],dmriprep:[0,19,21,22],dmriprep_named_opt:19,doc:[17,19],docker:[1,17,18,22],dockerfil:[17,19],dockerout:22,document:[17,18,19,21],doe:[1,22],don:22,done:22,draft:21,drift:3,driven:[10,17],drop:[17,19],ds001771:17,dtype:[2,17],dump:1,dwi2t1w:22,dwi2t1w_init:1,dwi:[0,1,2,3,4,5,8,10,11,12,17,21,22],dwi_derivatives_wf:16,dwi_fil:[5,10,14,15],dwi_mask:[3,14,16],dwi_ref:16,dwi_refer:14,each:[1,12,18,22],earli:1,easi:18,easili:[1,18],eddi:[0,11,13,17,18,21,22],eddy_openmp:15,eddy_wf:15,edu:22,effect:22,effort:21,either:[1,18,22],els:21,email:18,enabl:[1,21,22],encod:10,encompass:18,end:18,engin:[1,19],enh:17,enlist:1,ensembl:21,ensur:[5,18,22],entiti:[2,12,22],environ:[1,17,18,22],epi:22,equip:18,equival:21,erin:17,error:[1,17,22],escienc:17,esteban:17,estim:[1,3,10,15,17,21,22],etc:[1,18],evalu:[10,21],even:22,event:[21,22],everi:1,exact:22,exampl:[1,3,5,9,10,15,18,19,22],except:18,exclus:[5,21],exec_docker_vers:1,exec_env:[1,7],execut:[1,12,17,18,19,21],exercis:17,exist:[1,2,3,4,5,22],exit:22,expect:21,experi:21,explain:18,explicit:17,explor:21,express:18,extern:18,extra:19,extract:[1,2,3,8],extract_b0:[3,8],extractb0:3,eye:10,fact:[17,22],factor:3,fair:17,fals:[1,2,10,14,15,16],familiar:18,fast:[1,17],favour:17,fbed:1,featur:[17,22],februari:18,feel:18,field:1,fieldmap:[1,2,14,17,21,22],figure1:17,file:[1,2,3,4,5,10,14,15,16,17,18,19,22],filenam:[1,10],filesystem:1,filetyp:10,filter:[1,18],find:18,finish:21,first:[1,17,19,21,22],fit:18,fix:[1,2,17,22],fixed_hdr:2,flag:[1,17,21,22],flair:2,flake8:17,flat:1,flexibl:17,flow:18,flowchart:17,fmap:[2,14],fmap_bsplin:1,fmap_coeff:14,fmap_demean:1,fmap_id:14,fmap_mask:14,fmap_ref:14,fmriprep:[17,18,21,22],focu:21,folder:[1,12,22],follow:[17,19,21,22],forc:22,force_syn:1,forkserv:1,form:[5,22],format:[1,18],forward:17,found:[1,17,19,22],frame:10,framewis:21,framework:19,free:[1,18,19,22],free_mem:1,freesurf:[1,4,12,17,18,19],freesurfer_hom:22,from:[1,2,3,8,17,18,19,21,22],from_dict:1,from_fil:[3,4,5],front:17,fs_licens:22,fs_license_fil:1,fs_subjects_dir:1,fsl:[15,17,19,21],full:[1,10,12,17],full_spher:5,fullds005:22,fund:22,further:[21,22],futur:[18,21,22],garikoitz:17,gen_eddy_textfil:15,gener:[1,4,15,17,18,19,21,22],generate_rasb:10,generate_vecv:10,get:[1,10,19,22],get_linked_lib:1,get_plugin:1,gf5080e9a:[1,22],gibb:21,gihub:17,git:18,github:[17,18,22],given:[1,10,22],going:17,googl:[1,18],govern:18,gradient:[5,10,14,21],gradients_rasb:14,graph:[1,12,14,22],gre:22,grid:22,guid:21,guidelin:[17,18,21],habitu:19,half:10,halford:17,hand:19,handl:[5,7,8,18,19],happen:1,happi:18,hard:1,harvard:22,has:[1,9,18,19],has_fieldmap:14,hash:1,have:[10,19,21,22],head:[15,18,21],header:[1,2,22],health:17,hello:19,help:[18,22],hemispher:10,heurist:1,high:18,highli:22,hire:[1,22],hoc:18,holder:21,home:[1,22],honor:17,hospit:17,host:[19,22],hous:21,how:19,hpc:18,html:[1,4,10,22],http:[10,18,19,22],hub:19,idea:[18,19],identif:[17,21],identifi:[1,19,21,22],idiosyncrasi:18,ignor:[1,22],imag:[0,2,4,6,10,15,17,19,21,22],implement:[1,2,17,18,21],impli:[18,22],improv:[17,19,22],imput:21,in_bval:[5,14],in_bvec:[5,14],in_fil:[2,3,8,15],in_meta:15,in_rasb:5,includ:[17,18,21,22],inconsist:17,increas:22,index:[3,15],indic:22,individu:17,infer:18,info:1,inform:[0,1,12,22],infrastructur:[17,19],inhomogen:21,init:[1,22],init_dmriprep_wf:12,init_dwi_derivatives_wf:[14,16],init_dwi_preproc_wf:14,init_eddy_wf:15,init_reportlets_wf:[14,16],init_single_subject_wf:12,init_spac:1,initi:[1,17,21,22],input:[2,3,4,5,7,8,12,14,15,16,22],input_bids_path:19,instal:[1,18,22],instanc:[1,12,17],instead:[17,21],institut:17,instruct:19,integ:[3,5],integr:[17,21],intend:22,intendedfor:17,intens:8,interest:21,interfac:[1,17,18,19],intermedi:[1,22],interpret:[18,19],intervent:18,introduc:18,inventori:18,investig:21,invit:21,iowa:17,isbi:21,ismrm:21,issu:[1,17,18,21],item:[2,3,4,5,17],iter:[1,17],jame:17,januari:18,jell:17,join:1,joseph:17,json:[1,22],just:10,keep:[1,21,22],kei:[2,22],kent:17,kernel:[1,19],keshavan:17,keyword:22,kind:18,known:19,krembil:17,kwarg:2,label:[12,14,22],languag:[17,18],laptop:18,larg:[17,18],last:[8,10],latest:[18,21,22],latex:[1,22],lausann:17,law:18,layout:[1,22],learn:18,least:22,left:[1,2,21],leftov:17,length:10,lerma:17,less:[1,17,21,22],level:[1,19,22],librari:[1,18],licens:[1,17,19],lie:10,lightweight:19,like:[1,18,21],limit:[1,18,19,22],line:[1,18,19,21],linear:21,lineno:1,link:[1,17],lint:17,linux:[1,19],list:[1,2,3,4,5,10,12,18,19,22],load:[1,17],loadtxt:5,local:[17,22],locat:[10,16,22],log:[0,18,22],log_dir:1,log_level:1,logger:1,logitudin:1,longitudin:[1,22],look:[1,18],low:[10,22],low_mem:1,machin:19,magic:1,mai:[12,17,18,22],maint:17,maintain:[1,18],mainten:17,make:[9,10,18,19,21],makefil:17,manag:1,mandatori:[2,3,5],mani:19,mansour:17,manual:[18,22],manuscript:17,map:[17,18,22],march:18,mark:17,markdown:1,mask:[3,10,14,16,21],mask_fil:[3,8,10],master:22,matter:21,mattermost:[18,21],matthew:17,maximum:22,maxtasksperchild:1,md_only_boilerpl:1,mean:[1,10,22],measur:21,median:8,medicin:17,meet:21,mem:22,mem_mb:22,memori:[1,22],memory_gb:[1,22],mental:17,messag:[1,19],meta_dict:2,metadata:2,metal:19,method:[0,19,22],mgh:22,mgr:1,michael:17,migrat:17,mileston:[17,18],millimet:22,miniconda:17,minim:[1,17],minor:17,misc:[0,6],miscellan:9,modal:14,mode:[1,17],model:[18,21],modifi:[19,22],modul:[0,1,2,6,11,13,17],monitor:[1,22],month:21,monthli:21,more:[17,18,19,21],most:[10,17,19,21],mostli:21,motion:[15,18,21],move:17,mri:[12,14,18],multi:19,multipl:21,multiproc:1,multiprocess:1,multithread:1,music:21,must:[1,10,19,22],mutual:5,n_cpu:22,name:[2,15,16,17,18,19],named_opt:19,ndarrai:10,necessari:19,need:[1,12],neurodock:19,neurohackademi:17,neuroimag:[18,19],neuroinformat:17,neurosci:17,neuroscientist:18,neurostar:18,newer:18,newrasb:5,next:19,nice:18,nifti:[1,2,14,15],nii:[3,5,15],niprep:[17,19,22],nipyp:[1,2,3,4,5,17,18,19,22],nipype_vers:1,niworkflow:[2,7,17],nlmean:21,nmr:22,node:[1,22],nois:21,noisi:21,non:[1,4,10,21,22],none:[1,2,3,4,5,8,10],nonlinear:22,nonstandard:1,norm:10,norm_val:10,norm_vec:10,normal:[10,14,22],normalize_gradi:10,note:[21,22],notebook:21,notrack:[1,22],notrecommend:22,now:22,nproc:[1,17,22],nstd_space:4,nthread:22,number:[1,10,12,21,22],numer:18,numpi:[2,10],oasis30:1,object:[1,2,3,4,5,10],obtain:[18,19,22],occurr:22,octob:[18,21],oesteban:1,off:21,offici:21,oldrasb:5,omp:22,omp_nthread:[1,22],on_fail:17,onc:19,one:[12,14,22],ones:10,ongo:21,onli:[1,21,22],onlin:22,oper:[1,10,19,22],oppos:12,opt:[1,22],option:[1,2,4,5,17,18,19,21],orchestr:14,order:21,org:[18,22],organ:12,orient:[10,22],origin:22,oscar:17,osf:17,other:[0,17,18,19,21],otherwis:1,othewis:10,our:[17,18,19,21],out:[1,17,19,22],out_acqparam:15,out_b0:3,out_bval:5,out_bvec:5,out_dict:2,out_eddi:15,out_fil:[2,3],out_index:15,out_meta:2,out_path:8,out_path_bas:2,out_rasb:5,out_ref:3,out_report:4,outcom:[21,22],outlier:21,output:[0,1,2,3,4,5,11,13,14,15,17,18,19,22],output_dir:[1,16,22],output_spac:[1,22],over:[1,3,17],overal:18,overcommit:1,overcommit_limit:1,overcommit_polici:1,overdu:17,overhaul:17,packag:[0,17,18,19],page:17,pair:10,pandoc:22,parallel:1,paramet:[1,10,12,14,15,16,22],parameter:1,parameterize_dir:1,part:[21,22],particip:[1,22],participant_id:1,participant_label:[1,7,22],particular:[1,18],pass:[1,22],patch2self:21,patch:2,path:[1,2,10,14,15,17,19,22],pathlik:[2,3,4,5,12,14],pca:21,pdf:[12,14],pennsylvania:17,pepolar:[17,22],per:22,perelman:17,perform:[12,18],permiss:18,phase:21,phaseencodingdirect:15,philosophi:[18,21],pickl:1,pin:17,pip:19,pipelin:[12,17,18],pisner:17,place:21,plan:[1,18],platform:1,pleas:[17,18,19,21,22],plot:21,plugin:[1,17,22],plugin_arg:1,png:[12,14],point:[10,22],poldrack:17,pole:[5,10],polici:1,pop:18,popul:12,popular:19,popylar:[17,22],port:[17,21],posit:18,posix:1,posixpath:1,possibl:[1,22],preambl:19,prefer:21,prefix:[9,22],premier:21,prep:17,prepar:[12,17,18,22],preprocess:[1,12,14,17,18],present:[9,21],pretti:21,previou:[18,22],price:19,princip:22,principl:17,pro:18,probabl:19,process:[1,12,14,17,18,21,22],produc:19,program:[17,18,22],project:[1,18],promin:21,propag:2,properti:10,propos:21,protocol:21,provid:[18,21,22],psychiatri:17,psycholog:17,pub:10,pull:19,pybid:22,pypi:19,python:[1,17,18],qsiprep:21,qualiti:[18,22],queri:18,question:18,radiolog:17,rais:17,raise_error:10,raise_inconsist:10,raise_insuffici:1,ram:1,random:22,rapid:18,rasb:[10,14],rasb_dwi_length_check:10,rasb_fil:10,raw:10,reach:21,read:[1,19,21],read_text:15,readi:[19,21],readm:17,real:22,realli:10,reason:[19,22],recent:10,recommend:[18,22],recon:[1,12,22],reconal:22,reconstruct:[1,22],record:22,redirect:1,redirect_warn:1,reduc:22,refactor:17,refer:[1,10,14,16,17,22],regard:[1,21],regardless:12,regist:[1,14,22],registr:[17,18],registri:17,regular:1,rel:[10,19],relat:18,releas:[18,21],remov:[1,17,22],reorgan:17,reorient:[10,17],reorient_rasb:10,replac:[1,7,21],replic:22,repo:21,report:[0,1,2,12,16,17,21,22],reportlet:[1,4,16,17,22],reportlets_wf:16,reports_bug:17,reports_onli:1,repres:[1,2,3,4,5],represent:[1,17],reproduc:18,requir:[18,19,22],rero:21,rerun:22,res:[3,22],resampl:22,rescal:[3,8],rescale_b0:[3,8],rescaleb0:3,research:[18,21],resolut:22,resourc:[1,22],resource_monitor:[1,3,4,5],respons:[0,18],result:[1,10,18,22],resultinb:10,retriev:22,retval:1,reus:22,revis:17,richi:17,rician:21,right:16,ring:21,road:[17,18],roadmap:[17,18],robust:18,roi:2,rokem:17,roll:17,root:[1,22],rootlogg:1,rstudio:10,rtol:5,run:[1,3,5,12,14,17,19,21,22],run_reconal:1,run_unique_id:1,run_uuid:[1,22],runtim:[1,22],russel:17,salient:17,salim:[17,21],same:19,sampl:22,save:[2,16,17],sbref:[2,22],scale:14,scan:17,schedul:21,school:17,score:10,scott:18,script:17,sdc:22,sdc_report:16,sdcflow:[17,21],search:22,section:[0,18,19],secur:19,see:[1,18,19,22],seed:[1,22],segment:4,sei:22,select:[1,22],send:22,sent:19,sentri:17,separ:[12,22],septemb:18,seri:[3,10,18,22],serv:[16,17,21],session:[1,12,17],set:[1,12,16,17,18,19,21,22],sever:[12,21],sfm:21,sha256:1,shape:10,share:[1,19],shell:[10,21],shorelin:21,should:[1,2,19,21,22],show:[17,19,22],signal:[3,8,10],signal_drift:3,simpleinterfac:[2,3,4,5],simpli:22,simplic:17,singl:[1,12,21,22],singleton:1,singular:[18,22],skip:22,skiprow:5,skull:[1,22],skull_strip_fixed_se:1,skull_strip_templ:[1,22],skullstrip:17,sloppi:[1,17,22],small:17,smoke:17,smriprep:[1,17],snowbal:18,softwar:[18,19,21,22],solid:21,solut:21,some:[1,17,18,19,21,22],someth:19,somewher:18,sort:21,sourc:[2,12,14],source_fil:[2,16],space:[1,4,18,22],spatial:[1,22],spatialrefer:1,specif:[0,17,18,21],specifi:[19,22],speed:22,sphere:10,spline:1,sprint:[17,21],squar:10,stabl:21,stage:22,stake:21,standard:[1,4,10,18,22],stanford:17,start:[1,17,18,19,21],state:18,statist:22,std_space:4,step:[1,17,18,19,21],still:18,stop:[1,22],stop_on_first_crash:1,store:[1,2,16,22],str:[1,2,3,5,10,12,15,16],stream:19,string:[1,2,3,4,5],strip:[1,22],structur:[1,2,4,10,19,22],sty:17,sub:[1,9,12,17,22],sub_prefix:9,subid:9,subject:[1,4,9,12,22],subject_data:2,subject_id:[2,4,12],subjects_dir:[4,12],subjectsummari:4,submit:[17,18],submm:22,submodul:[0,18],suboptim:1,subpackag:[0,18],subprocess:1,successfulli:22,suffici:22,suffix:22,summari:4,summaryinterfac:4,support:[17,18,21],sure:[9,18,19,21],surfac:[1,18],surfer:22,suscept:[1,14,18],svg:[12,14,17],syn:18,system:[9,19,22],t1w:[2,4,17,21,22],t2w:[2,4],tabl:[5,10,14],tacc:19,tag:17,take:[18,21,22],target:[1,17,18],task:[1,17],task_id:17,team:21,techniqu:21,technolog:18,templat:[1,12,22],templateflow:1,templateflow_hom:1,templateflow_vers:1,temporari:[17,21],tenant:19,term:18,termin:19,test:[17,21,22],texa:17,text:1,thei:21,them:[17,21],therefor:19,thi:[1,9,10,12,17,18,19,21,22],thp0005:1,thp002:1,thread:22,threshold:10,through:[21,22],time:[1,3,22],tip:19,tmp:1,tmpdir:[3,5],to_filenam:[1,10],tolist:10,tomatch:2,toml:1,took:19,tool:[1,3,17,18,19,22],top:22,topup:17,toronto:17,totalreadouttim:15,toward:21,traceback:10,track:[1,17,18],transform:10,transpar:18,travisci:17,treat:22,trick:[1,19],tsv:5,tupl:5,tutori:21,two:[12,19],txt:[1,22],type:10,typo:17,ubuntu:19,uncompress:[1,2],under:[1,18,19],uniqu:1,unit:[10,17],univers:17,unless:[18,22],unmodifi:2,until:21,updat:[17,18,21],upon:18,upper:22,upstream:17,usa:17,usabiaga:17,usag:[0,17,18,19],use:[1,17,18,19,21,22],use_plugin:22,use_syn:1,used:[1,14,19,21,22],useful:1,user:[1,19,21],uses:22,using:[1,8,12,17,19,21,22],usr:1,util:[0,1,17,18],uuid:22,val:17,valid:[18,19,22],validate_input_dir:7,valu:[1,2,5,10,14,22],valueerror:10,variabl:[1,22],variat:10,varieti:18,vec:[10,17],vector:[0,2,6,14,17],veraart:17,verbos:[1,22],veri:22,version:[1,4,7,17,18,19,22],via:[1,22],video:[17,18],virtual:[1,18,19],visit:19,visual:22,volum:[3,8,10,21,22],voxel:21,vstack:10,vvv:22,wai:[10,19,21],want:[18,22],warn:1,warranti:18,washington:17,websit:17,weekli:21,weight:10,welcom:18,well:21,were:19,what:18,when:[1,17,22],whenev:1,where:[1,10,18,21,22],whether:[1,2,10,21,22],which:[1,2,3,4,5,10,16,17,18,19,21,22],white:21,who:21,whole:18,wide:1,within:[10,19,21],without:[18,22],work:[1,17,19,21,22],work_dir:[1,22],workdir:22,workflow:[0,1,9,17,18,19],world:[19,22],would:21,wrap:21,write:[1,10,16,17,18,22],write_derivative_descript:7,write_graph:1,written:[1,19],www:[18,22],xxxxx:22,year:17,york:17,you:[18,19,21,22],your:[18,19,22],yourself:18,z_thre:10,zenodo:17,zero:10},titles:["Library API (application program interface)","dmriprep.config package","dmriprep.interfaces package","dmriprep.interfaces.images module","dmriprep.interfaces.reports module","dmriprep.interfaces.vectors module","dmriprep.utils package","dmriprep.utils.bids module","dmriprep.utils.images module","dmriprep.utils.misc module","dmriprep.utils.vectors module","dmriprep.workflows package","dmriprep.workflows.base module","dmriprep.workflows.dwi package","dmriprep.workflows.dwi.base module","dmriprep.workflows.dwi.eddy module","dmriprep.workflows.dwi.outputs module","What\u2019s new?","dMRIPrep","Installation","&lt;no title&gt;","Development road-map","Usage"],titleterms:{"1a0":17,"long":21,"new":17,The:22,about:18,analyt:22,ant:22,api:0,applic:0,april:21,argument:22,author:17,base:[12,14,17],befor:21,bid:[7,22],cloud:19,command:22,commerci:19,config:1,configur:[1,22],contain:19,content:18,correct:22,decemb:17,depend:19,develop:21,distort:22,dmriprep:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],docker:19,dwi:[13,14,15,16],eddi:15,end:21,environ:19,execut:22,extern:19,februari:21,filter:22,format:22,framework:18,freesurf:22,get:18,googl:22,handl:22,hpc:19,imag:[3,8],inform:18,instal:19,interfac:[0,2,3,4,5],involv:18,januari:[17,21],laptop:19,latest:17,librari:0,licens:[18,22],line:22,list:17,log:1,mai:21,manual:19,map:21,march:[17,21],misc:9,modul:[3,4,5,7,8,9,10,12,14,15,16],name:22,niprep:18,novemb:17,octob:17,option:22,other:[1,22],output:16,packag:[1,2,6,11,13],paper:17,perform:22,plan:21,posit:22,prepar:19,preprocess:22,previou:17,program:0,python:19,queri:22,recommend:19,registr:22,releas:17,report:4,respons:1,road:21,section:1,septemb:[17,21],seri:17,singular:19,specif:22,submodul:[2,6,11,13],subpackag:11,surfac:22,syn:22,target:21,technolog:19,term:21,track:22,usag:[1,22],util:[6,7,8,9,10],vector:[5,10],version:21,what:17,workflow:[11,12,13,14,15,16,22]}})