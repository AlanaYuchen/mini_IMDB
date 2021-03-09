CREATE TABLE title_basics(
tconst varchar,
titleType varchar,
primaryTitle varchar,
originalTitle varchar,
isAdult INT,
startYear INT,
endYear INT,
runtimeMinutes INT,
genres varchar(255),
PRIMARY KEY (tconst));

CREATE TABLE title_principals(
tconst varchar,
ordering int,
nconst varchar,
category varchar,
job varchar,
characters varchar);
CREATE TABLE name_basics(
nconst varchar,
primaryNmae varchar,
birthyear int,
deathyear int,
primaryProfession varchar,
knownForTitles varchar);

CREATE TABLE title_ratings(
tconst varchar(20),
averageRating DEC(5,2),
numVotes INT,
PRIMARY KEY (tconst));

DROP TABLE title_ratings;

SELECT title_basics.primaryTitle, title_basics.startYear FROM title_basics
INNER JOIN title_priincipals
ON title_priincipals.tconst=title_basics.tconst
INNER JOIN name_basics
ON title_priincipals.nconst=name_basics.nconst
WHERE (startYear>2000 OR startYear is NULL) AND (endYear<2020 or endYear is NULL)AND name_basics.primaryNmae='Malkeet Rauni';

SELECT * FROM title_priincipals WHERE tconst='tt8852130';
SELECT * FROM name_basics WHERE nconst='nm3608767';

CREATE FUNCTION previous_ratingAve(N_const VARCHAR, Year INT)
RETURNS NUMERIC(4,2) AS
$$ BEGIN
RETURN (
	SELECT CAST (AVG(averagerating) AS NUMERIC(4,2)) FROM title_ratings
	WHERE tconst IN (
		SELECT tconst FROM title_basics
		WHERE tconst IN (SELECT UNNEST(knownForTitles) FROM name_basics
					 		WHERE nconst = N_const)
		AND startyear < Year
		)
	);
END; $$
LANGUAGE plpgsql;

CREATE FUNCTION get_name(N_const VARCHAR)
	RETURNS VARCHAR AS
$$ BEGIN
RETURN (SELECT primaryname FROM name_basics WHERE nconst = N_const);
END;$$
LANGUAGE plpgsql;

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

CREATE FUNCTION test(l VARCHAR[], year INT)
RETURNS TABLE (
 T_consts VARCHAR[]
) AS
$$ BEGIN
RETURN QUERY SELECT array_agg(title_basics.tconst) FROM title_basics
  INNER JOIN title_principals
  ON title_principals.tconst = title_basics.tconst
  WHERE title_principals.nconst IN (SELECT UNNEST(l))
  AND startyear < year
  GROUP BY title_principals.nconst;
END;$$
LANGUAGE plpgsql;


SELECT test(ARRAY ['nm5568493', 'nm3608767', 'nm5679766', 'nm10047651', 'nm9989238', 'nm3800091', 'nm9989231', 'nm10047650'], 2018);

DROP FUNCTION test;

SELECT UNNEST(ARRAY ['nm5568493', 'nm3608767', 'nm5679766', 'nm10047651', 'nm9989238', 'nm3800091', 'nm9989231', 'nm10047650']);
SELECT unnest FROM UNNEST(ARRAY ['nm5568493', 'nm3608767', 'nm5679766', 'nm10047651', 'nm9989238', 'nm3800091', 'nm9989231', 'nm10047650'])
