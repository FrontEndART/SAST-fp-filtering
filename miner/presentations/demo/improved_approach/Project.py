import os


class Project:
    __PROJ_LOCAL_REPO = os.path.join("{tmp_dir}", "local_repo", "{project_name}")

    __PROJ_CODE_CHG = os.path.join("{tmp_dir}", "code_chg", "{project_name}")
    __PROJ_CMT_RANK = os.path.join(
        "{tmp_dir}",
        "cmt_rank",
        "{project_name}",
    )

    __PROJ_TOP_CMT = os.path.join("{tmp_dir}", "top_cmt", "{project_name}")

    __PROJ_PMD_REPORT = os.path.join("{tmp_dir}", "pmd_report", "{project_name}")

    __PROJ_WARN_DB = os.path.join("{warn_db}", "{project_name}")

    def __init__(self, repo_url, tmp_dir, warn_db):
        self.repo_url = repo_url
        self.tmp_dir = tmp_dir
        self.warn_db = warn_db

    def get_name(self):
        return self.repo_url.split(".git")[0].split("/")[-1]

    def get_local_repo(self):
        return self.__PROJ_LOCAL_REPO.format(
            tmp_dir=self.tmp_dir, project_name=self.get_name()
        )

    def get_code_chg_dir(self, abs_path=True):
        if abs_path:
            return self.__PROJ_CODE_CHG.format(
                tmp_dir=self.tmp_dir, project_name=self.get_name()
            )
        else:
            return self.__PROJ_CODE_CHG.format(
                tmp_dir=".", project_name=self.get_name()
            )

    def get_cmt_rank_dir(self, abs_path=True):
        if abs_path:
            return self.__PROJ_CMT_RANK.format(
                tmp_dir=self.tmp_dir, project_name=self.get_name()
            )
        else:
            return self.__PROJ_CMT_RANK.format(
                tmp_dir=".", project_name=self.get_name()
            )
            
    def get_cmt_rank(self):
        return os.path.join(self.get_cmt_rank_dir(), "cmt_rank.json")

    def get_top_cmt_dir(self):
        return self.__PROJ_TOP_CMT.format(
            tmp_dir=self.tmp_dir, project_name=self.get_name()
        )

    def get_top_cmt(self):
        return os.path.join(self.get_top_cmt_dir(), "top_cmt.json")

    def get_pmd_report_dir(self):
        return self.__PROJ_PMD_REPORT.format(
            tmp_dir=self.tmp_dir,
            project_name=self.get_name(),
        )

    def get_warn_db_dir(self):
        return self.__PROJ_WARN_DB.format(
            warn_db=self.warn_db,
            project_name=self.get_name(),
        )
        
    def get_warn_db(self):
        return os.path.join(self.get_warn_db_dir(), "warn_db.csv")
