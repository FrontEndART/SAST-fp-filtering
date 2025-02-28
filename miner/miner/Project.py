import os


class Project:
    __PROJ_LOCAL_REPO = os.path.join("{tmp_dir}", "local_repo")

    __PROJ_CODE_CHG = os.path.join("{tmp_dir}", "code_chg")
    __PROJ_CMT_RANK = os.path.join(
        "{tmp_dir}",
        "cmt_rank"
    )

    __PROJ_TOP_CMT = os.path.join("{tmp_dir}", "top_cmt")

    __PROJ_DEPS = os.path.join("{tmp_dir}", "dependencies")

    __PROJ_SCA_REPORT = os.path.join("{tmp_dir}", "{sca}_report")

    __PROJ_WARN_DB = os.path.join("{warn_db}", "{project_name}")

    __PROJ_DATASET = os.path.join("{warn_db}", "{project_name}", "dataset")

    def __init__(self, repo_url, tmp_dir, warn_db):
        self.repo_url = repo_url
        self.tmp_dir = tmp_dir
        self.warn_db = warn_db

    def get_name(self):
        return self.repo_url.split(".git")[0].split("/")[-1]

    def get_local_repo(self):
        return self.__PROJ_LOCAL_REPO.format(
            tmp_dir=self.tmp_dir
        )

    def get_code_chg_dir(self):
        return self.__PROJ_CODE_CHG.format(
            tmp_dir=self.tmp_dir
        )

    def get_cmt_rank_dir(self):
        return self.__PROJ_CMT_RANK.format(
            tmp_dir=self.tmp_dir
        )

    def get_cmt_rank(self):
        return os.path.join(self.get_cmt_rank_dir(), "cmt_rank.json")

    def get_top_cmt_dir(self):
        return self.__PROJ_TOP_CMT.format(
            tmp_dir=self.tmp_dir
        )

    def get_top_cmt(self):
        return os.path.join(self.get_top_cmt_dir(), "top_cmt.json")

    def get_deps_dir(self):
        return self.__PROJ_DEPS.format(
            tmp_dir=self.tmp_dir
        )

    def get_sca_report_dir(self, tool):
        return self.__PROJ_SCA_REPORT.format(
            tmp_dir=self.tmp_dir,
            sca=tool,
        )

    def get_warn_db_dir(self):
        return self.__PROJ_WARN_DB.format(
            warn_db=self.warn_db,
            project_name=self.get_name(),
        )

    def get_tp_warn_db(self, tool):
        return os.path.join(self.get_warn_db_dir(), f"{tool}_tp_warn_db.csv")

    def get_fp_warn_db(self, tool):
        return os.path.join(self.get_warn_db_dir(), f"{tool}_fp_warn_db.csv")

    def get_dataset_dir(self):
        return self.__PROJ_DATASET.format(
            warn_db=self.warn_db,
            project_name=self.get_name(),
        )
