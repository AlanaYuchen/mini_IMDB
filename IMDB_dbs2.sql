CREATE FUNCTION get_nconst(T_const VARCHAR)
RETURNS TABLE (
	nconst VARCHAR,
	category VARCHAR
	) AS 
$$ BEGIN
RETURN QUERY SELECT title_principals.nconst, title_principals.category
	FROM title_principals
WHERE tconst = T_const
AND (title_principals.category = 'actor'
	 OR title_principals.category = 'actress' 
	 OR title_principals.category = 'composer' 
	 OR title_principals.category = 'director'
	 OR title_principals.category = 'writer')
ORDER BY category;
END; $$
LANGUAGE plpgsql;

CREATE FUNCTION previous_ratingAve(T_consts VARCHAR[])
RETURNS NUMERIC(4,2) AS
$$ BEGIN
RETURN (
	SELECT CAST (AVG(averagerating) AS NUMERIC(4,2)) FROM title_ratings
	WHERE tconst IN (SELECT UNNEST T_consts)
	);
END; $$
LANGUAGE plpgsql;

CREATE FUNCTION get_name(N_const VARCHAR)
	RETURNS VARCHAR AS
$$ BEGIN
RETURN (SELECT primaryname FROM name_basics WHERE nconst = N_const);
END;$$
LANGUAGE plpgsql;

CREATE FUNCTION get_tconst_on_nconst_list(l VARCHAR[], year INT)
RETURNS TABLE (
	T_consts VARCHAR,
	N_consts VARCHAR
) AS
$$ BEGIN
RETURN QUERY SELECT title_basics.tconst, title_principals.nconst FROM title_basics
		INNER JOIN title_principals
		ON title_principals.tconst = title_basics.tconst
		WHERE title_principals.nconst IN (SELECT UNNEST(l))
		AND startyear < year;
END;$$
LANGUAGE plpgsql;

Drop function get_nconst;

CREATE FUNCTION previous_ratingAve(T_consts VARCHAR[])
RETURNS NUMERIC(4,2) AS
$$ BEGIN
RETURN (
 SELECT CAST (AVG(averagerating) AS NUMERIC(4,2)) FROM title_ratings
 WHERE tconst IN (SELECT UNNEST (T_consts))
 );
END; $$
LANGUAGE plpgsql;

CREATE TABLE name_basics(
nconst varchar,
primaryName varchar,
birthyear int,
deathyear int,
primaryProfession varchar,
knownForTitles varchar);

SELECT * FROM name_basics;
SELECT * FROM title_basics; 

