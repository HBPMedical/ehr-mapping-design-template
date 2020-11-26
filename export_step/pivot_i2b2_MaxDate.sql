﻿create or replace function pivotfunction_max() RETURNS void AS $BODY$
-- ******** OFFICIAL max date one visit per patient export plpg function 4 i2b2-harmonized db ********
DECLARE concept text;
DECLARE valtype text;
DECLARE type_name text;
DECLARE query text;
DECLARE cdesQuery text;
DECLARE table_name text;
DECLARE char_val text;
DECLARE num_val numeric(18,5);
DECLARE usedid text;
DECLARE currentid text;
DECLARE countCDEcolumns integer;
DECLARE startdate timestamp without time zone;
DECLARE subjectcode integer;
DECLARE subjectcodeide text;
DECLARE subjectageyears integer;
DECLARE subjectage numeric(18,5);
DECLARE gender text;
DECLARE dataset text;
DECLARE dataset_const text;
DECLARE agegroup text;-- in this pivotfunction version agegroup s value is still calculated here (considering the harmonized i2b2 does NOT have it).. in the next version (NEW2) we will consider that the harmonized i2b2 already has calculated it ---> 01-12-2019: Changed my mind on that...
DECLARE encounter text;
DECLARE countUpdates integer;
DECLARE countInserts integer;
declare
    v_state   TEXT;
    v_msg     TEXT;
    v_detail  TEXT;
    v_hint    TEXT;
    v_context TEXT;
BEGIN
query := '';
usedid := '';
countUpdates := 0;
countInserts := 0;
cdesQuery := ''; countCDEcolumns :=0;

for concept in
	SELECT concept_cd FROM concept_dimension WHERE sourcesystem_cd='CDE' ORDER BY upload_id --in the mapping-task we have to have filled in upload_id with the sequence of the cde columns !!!!
loop
	cdesQuery := cdesQuery || ', "' || concept || '" text';
	countCDEcolumns := countCDEcolumns+1;
	raise notice 'CDE: %', concept;
end loop;
raise notice 'Counted % CDE-columns', countCDEcolumns;
-- create table for cde variables - the list of variables in this table is fixed (cde variables)
table_name := 'new_table';
query := 'CREATE TABLE ' || table_name || '( "subjectcode" text' || cdesQuery;

-- collect all hospital specific concept_cds in order to obtain the available columns
--raise notice '1. Here is the CREATE TABLE query: %', query;
for concept, valtype in 
	select distinct on (concept_cd) concept_cd, valtype_cd 
	from observation_fact
loop
CASE
    WHEN 'N'=valtype THEN
	type_name := ' numeric(18,5)';
    WHEN 'T'=valtype THEN
	type_name := ' text';
    ELSE 
	type_name := NULL; -- *****
END CASE;
if query = '' then
	query := query || '"' || concept || '"' || type_name ;
else
	-- if the concept_cd has not been inserted before
	if query not like ('%"' || concept || '"%') then
		-- add it in the create statement
		query := query || ',' || '"' || concept || '"' || type_name ;
	end if;
end if;
end loop;
--raise notice '2. Here is the CREATE TABLE query: %', query;
-- add primary key
query := query || ', PRIMARY KEY (subjectcode))';
--raise notice '3. And here it is now: %', query;
-- execute statement
execute format('DROP TABLE IF EXISTS ' || table_name);
--raise notice '4. And here it is now just before it runs..: %', query;
execute format(query);
/*
EXECUTE FORMAT('DROP VIEW IF EXISTS max_age');
EXECUTE FORMAT('CREATE VIEW min_age AS SELECT patient_num, min(patient_age) AS minage FROM visit_dimension GROUP BY patient_num');*/
EXECUTE FORMAT('DROP VIEW IF EXISTS max_date');
EXECUTE FORMAT('CREATE VIEW max_date AS SELECT patient_num, max(start_date) AS maxdate FROM visit_dimension GROUP BY patient_num');
EXECUTE FORMAT('DROP VIEW IF EXISTS max_date_with_age');
EXECUTE FORMAT('CREATE VIEW max_date_with_age AS SELECT md.patient_num, pm.patient_ide, vd.encounter_num, md.maxdate, vd.patient_age 
		FROM max_date md, visit_dimension vd, patient_mapping pm 
		WHERE md.patient_num=vd.patient_num AND md.maxdate=vd.start_date AND md.patient_num=pm.patient_num');

EXECUTE 'SELECT DISTINCT(provider_id) FROM observation_fact LIMIT 1' INTO dataset_const;--supposedly provider has only one value... We ll give it to 'dataset' column.
raise notice 'dataset variable has value: %', dataset_const;
-- Table has been created. Time to insert tuples...  <--- CHANGE: subjectcode FROM NOW ON IS patient_ide NOT patient_num <---- !!!!

for subjectcodeide, subjectageyears, subjectage, gender in 
	select mdwa.patient_ide, FLOOR(vid.patient_age), ROUND((vid.patient_age-FLOOR(vid.patient_age))*12), pad.sex_cd
	from patient_dimension pad, visit_dimension vid, max_date_with_age mdwa 
	where mdwa.patient_num = pad.patient_num and mdwa.encounter_num = vid.encounter_num
        --order by patient_ide
LOOP
currentid := ',' || subjectcodeide || ',';

CASE 
	WHEN subjectageyears is null
		THEN agegroup = null;
	WHEN 50 <= subjectageyears and subjectageyears < 60
		THEN agegroup = '''50-59y''';
	WHEN 60 <= subjectageyears and subjectageyears < 70
		THEN agegroup = '''60-69y''';
	WHEN 70 <= subjectageyears and subjectageyears < 90
		THEN agegroup = '''70-79y''';
	WHEN 80 <= subjectageyears
		THEN agegroup = '''+80y''';
	ELSE
		agegroup = '''-50y''';
END CASE;

	IF ( usedid ~ currentid) then
	else
	     BEGIN

		execute format('insert into ' || table_name  || '( subjectcode, subjectageyears, subjectage, gender, dataset, agegroup) VALUES (''' || subjectcodeide || ''',' || subjectageyears || ',' || subjectage || ',''' || gender || ''',''' || dataset_const || ''',' || agegroup || ')');
		
		usedid := usedid || ',' || subjectcodeide ||',';
		countInserts=countInserts+1;
	    EXCEPTION WHEN others then
		RAISE NOTICE '~~~~~ NULL value in age or gender for subject: % ~~~~~ TERMINATING... ~~~~~', subjectcodeide;
		get stacked diagnostics
	        v_state   = returned_sqlstate,
        	v_msg     = message_text,
        	v_detail  = pg_exception_detail,
        	v_hint    = pg_exception_hint,
        	v_context = pg_exception_context;
		raise notice E'Got exception:
	        state  : %
        	message: %
        	detail : %
        	hint   : %
        	context: %', v_state, v_msg, v_detail, v_hint, v_context;
		RETURN;
	     END;
	end if;
END LOOP;
-- Demographics info has been stored
raise notice 'countInserts: %', countInserts;
-- Store data. For every concept_cd and every patient store the data that are the OLDEST
-- The only criteria of the encounter to choose is the date. If there are more than one encounter in the same day the choice is done randomly.
for concept in SELECT column_name FROM information_schema.columns WHERE information_schema.columns.table_name = 'new_table'
loop
	FOR subjectcodeide, encounter, startdate, valtype, char_val, num_val IN
	 (select mdwa.patient_ide, obf.encounter_num, obf.start_date, obf.valtype_cd, obf.tval_char, obf.nval_num 
	  from max_date_with_age as mdwa, observation_fact as obf
	  where mdwa.encounter_num = obf.encounter_num and concept_cd = concept)
	loop
		--raise notice 'valtype - char_val - num_val -patient_ide(subjectcode)-: % - % - % -%-', valtype, char_val, num_val, subjectcode;
		CASE
		    WHEN 'T'=valtype -- the problem is when valtype is NOT T and num_val IS NULL..... 
		    THEN
			IF char_val IS NULL THEN
				char_val = '';
			END IF;
			execute format('update ' || table_name  || ' set ' || '"' || concept || '" = ''' ||  char_val || ''' where subjectcode = ''' || subjectcodeide ||'''');		    
			countUpdates=countUpdates+1; 
		    WHEN 'N'=valtype
		    THEN	
			IF num_val IS NOT NULL THEN
				execute format('UPDATE ' || table_name  || ' set ' || '"' || concept || '" = ' ||  num_val || ' where subjectcode = ''' || subjectcodeide ||'''');
			countUpdates=countUpdates+1;
			END IF;		
			
		  --  ELSE			
			--execute format('UPDATE ' || table_name  || ' set ' || '"' || concept || '" = ' ||  NULL || ' where subjectcode = ' || subjectcodeide );			countUpdates=countUpdates+1;
		END CASE;
	end loop;
end loop;

raise notice 'CountUpdates: %', countUpdates;
--countUpdates := execute format('SELECT COUNT(*) FROM ' || table_name);
--raise notice 'new_table has % tuples', countUpdates;
EXECUTE FORMAT('DROP VIEW IF EXISTS max_date_with_age');--drop these views to have a "clean" db... so as not to have problems when altering types for the creation of the federation i2b2 db
EXECUTE FORMAT('DROP VIEW IF EXISTS max_date');		--

BEGIN
	COPY new_table FROM '/tmp/harmonized_clinical_data_max.csv' DELIMITER ',' CSV HEADER ; 
EXCEPTION
WHEN OTHERS 
        THEN raise notice 'No such file /tmp/harmonized_clinical_data_max.csv';
END;
COPY (SELECT * FROM new_table) TO '/tmp/harmonized_clinical_data_max.csv' WITH CSV DELIMITER ',' HEADER;
EXECUTE FORMAT('DROP TABLE IF EXISTS ' || table_name);
END; $BODY$ language plpgsql;
select pivotfunction_max();
