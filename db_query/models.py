# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING,
        blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class GcdAward(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField()
    deleted = models.IntegerField()
    modified = models.DateTimeField()
    notes = models.TextField()

    class Meta:
        managed = False
        db_table = 'gcd_award'


class GcdBiblioEntry(models.Model):
    story_ptr = models.OneToOneField('GcdStory', models.DO_NOTHING,
        primary_key=True)
    page_began = models.IntegerField(blank=True, null=True)
    page_ended = models.IntegerField(blank=True, null=True)
    abstract = models.TextField()
    doi = models.TextField()

    class Meta:
        managed = False
        db_table = 'gcd_biblio_entry'


class GcdBrand(models.Model):
    name = models.CharField(max_length=255)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    notes = models.TextField()
    url = models.CharField(max_length=255)
    issue_count = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_ended_uncertain = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_brand'


class GcdBrandEmblemGroup(models.Model):
    brand = models.ForeignKey(GcdBrand, models.DO_NOTHING)
    brandgroup = models.ForeignKey('GcdBrandGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_brand_emblem_group'
        unique_together = (('brand', 'brandgroup'),)


class GcdBrandGroup(models.Model):
    name = models.CharField(max_length=255)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    url = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    parent = models.ForeignKey('GcdPublisher', models.DO_NOTHING)
    issue_count = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_ended_uncertain = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_brand_group'


class GcdBrandUse(models.Model):
    publisher = models.ForeignKey('GcdPublisher', models.DO_NOTHING)
    emblem = models.ForeignKey(GcdBrand, models.DO_NOTHING)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'gcd_brand_use'


class GcdCreator(models.Model):
    gcd_official_name = models.CharField(max_length=255)
    whos_who = models.CharField(max_length=200, blank=True, null=True)
    birth_country_uncertain = models.IntegerField()
    birth_province = models.CharField(max_length=50)
    birth_province_uncertain = models.IntegerField()
    birth_city = models.CharField(max_length=200)
    birth_city_uncertain = models.IntegerField()
    death_country_uncertain = models.IntegerField()
    death_province = models.CharField(max_length=50)
    death_province_uncertain = models.IntegerField()
    death_city = models.CharField(max_length=200)
    death_city_uncertain = models.IntegerField()
    bio = models.TextField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    birth_country = models.ForeignKey('StddataCountry', models.DO_NOTHING,
        blank=True, null=True,
        related_name='%(class)s_birth_country')
    birth_date = models.ForeignKey('StddataDate', models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_birth_date')
    death_country = models.ForeignKey('StddataCountry', models.DO_NOTHING,
        blank=True, null=True,
        related_name='%(class)s_death_country')
    death_date = models.ForeignKey('StddataDate', models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_death_date')
    sort_name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.gcd_official_name} {self.whos_who}'

    class Meta:
        managed = False
        db_table = 'gcd_creator'


class GcdCreatorArtInfluence(models.Model):
    influence_name = models.CharField(max_length=200)
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING,
        related_name='%(class)s_creator')
    influence_link = models.ForeignKey(GcdCreator, models.DO_NOTHING,
        blank=True, null=True,
        related_name='%(class)s_influence_link')

    class Meta:
        managed = False
        db_table = 'gcd_creator_art_influence'


class GcdCreatorDegree(models.Model):
    degree_year = models.PositiveSmallIntegerField(blank=True, null=True)
    degree_year_uncertain = models.IntegerField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)
    degree = models.ForeignKey('GcdDegree', models.DO_NOTHING)
    school = models.ForeignKey('GcdSchool', models.DO_NOTHING, blank=True,
        null=True)

    class Meta:
        managed = False
        db_table = 'gcd_creator_degree'


class GcdCreatorMembership(models.Model):
    organization_name = models.CharField(max_length=200)
    membership_year_began = models.PositiveSmallIntegerField(blank=True,
        null=True)
    membership_year_began_uncertain = models.IntegerField()
    membership_year_ended = models.PositiveSmallIntegerField(blank=True,
        null=True)
    membership_year_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)
    membership_type = models.ForeignKey('GcdMembershipType', models.DO_NOTHING,
        blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gcd_creator_membership'


class GcdCreatorNameDetail(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)
    type = models.ForeignKey('GcdNameType', models.DO_NOTHING, blank=True,
        null=True)
    sort_name = models.CharField(max_length=255)
    is_official_name = models.IntegerField()
    in_script = models.ForeignKey('StddataScript', models.DO_NOTHING)
    family_name = models.CharField(max_length=255)
    given_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'gcd_creator_name_detail'


class GcdCreatorNonComicWork(models.Model):
    publication_title = models.CharField(max_length=200)
    employer_name = models.CharField(max_length=200)
    work_title = models.CharField(max_length=255)
    work_urls = models.TextField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)
    work_role = models.ForeignKey('GcdNonComicWorkRole', models.DO_NOTHING,
        blank=True, null=True)
    work_type = models.ForeignKey('GcdNonComicWorkType', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_creator_non_comic_work'


class GcdCreatorRelation(models.Model):
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    from_creator = models.ForeignKey(GcdCreator, models.DO_NOTHING,
        related_name='%(class)s_from_creator')
    relation_type = models.ForeignKey('GcdRelationType', models.DO_NOTHING)
    to_creator = models.ForeignKey(GcdCreator, models.DO_NOTHING,
        related_name='%(class)s_to_creator')

    class Meta:
        managed = False
        db_table = 'gcd_creator_relation'


class GcdCreatorRelationCreatorName(models.Model):
    creatorrelation = models.ForeignKey(GcdCreatorRelation, models.DO_NOTHING)
    creatornamedetail = models.ForeignKey(GcdCreatorNameDetail,
        models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_creator_relation_creator_name'
        unique_together = (('creatorrelation', 'creatornamedetail'),)


class GcdCreatorSchool(models.Model):
    school_year_began = models.PositiveSmallIntegerField(blank=True, null=True)
    school_year_began_uncertain = models.IntegerField()
    school_year_ended = models.PositiveSmallIntegerField(blank=True, null=True)
    school_year_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)
    school = models.ForeignKey('GcdSchool', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_creator_school'


class GcdCreatorSignature(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    name = models.CharField(max_length=255)
    notes = models.TextField()
    generic = models.IntegerField()
    creator = models.ForeignKey(GcdCreator, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_creator_signature'


class GcdCreditType(models.Model):
    name = models.CharField(unique=True, max_length=50)
    sort_code = models.IntegerField(unique=True)

    class Meta:
        managed = False
        db_table = 'gcd_credit_type'


class GcdDegree(models.Model):
    degree_name = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'gcd_degree'


class GcdFeature(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    name = models.CharField(max_length=255)
    sort_name = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    year_created = models.IntegerField(blank=True, null=True)
    year_created_uncertain = models.IntegerField()
    notes = models.TextField()
    feature_type = models.ForeignKey('GcdFeatureType', models.DO_NOTHING)
    language = models.ForeignKey('StddataLanguage', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_feature'


class GcdFeatureLogo(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    name = models.CharField(max_length=255)
    sort_name = models.CharField(max_length=255)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    notes = models.TextField()

    class Meta:
        managed = False
        db_table = 'gcd_feature_logo'


class GcdFeatureLogo2Feature(models.Model):
    featurelogo = models.ForeignKey(GcdFeatureLogo, models.DO_NOTHING)
    feature = models.ForeignKey(GcdFeature, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_feature_logo_2_feature'
        unique_together = (('featurelogo', 'feature'),)


class GcdFeatureRelation(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    notes = models.TextField()
    from_feature = models.ForeignKey(GcdFeature, models.DO_NOTHING,
        related_name='%(class)s_from_feature')
    relation_type = models.ForeignKey('GcdFeatureRelationType',
        models.DO_NOTHING)
    to_feature = models.ForeignKey(GcdFeature, models.DO_NOTHING,
        related_name='%(class)s_to_feature')

    class Meta:
        managed = False
        db_table = 'gcd_feature_relation'


class GcdFeatureRelationType(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    reverse_description = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'gcd_feature_relation_type'


class GcdFeatureType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'gcd_feature_type'


class GcdIndiciaPrinter(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    name = models.CharField(max_length=255)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    url = models.CharField(max_length=255)
    issue_count = models.IntegerField()
    country = models.ForeignKey('StddataCountry', models.DO_NOTHING)
    parent = models.ForeignKey('GcdPrinter', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_indicia_printer'


class GcdIndiciaPublisher(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('GcdPublisher', models.DO_NOTHING)
    country = models.ForeignKey('StddataCountry', models.DO_NOTHING)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    is_surrogate = models.IntegerField()
    notes = models.TextField()
    url = models.CharField(max_length=255)
    issue_count = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_ended_uncertain = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_indicia_publisher'


class GcdIssue(models.Model):
    number = models.CharField(max_length=50)
    volume = models.CharField(max_length=50)
    no_volume = models.IntegerField()
    display_volume_with_number = models.IntegerField()
    series = models.ForeignKey('GcdSeries', models.DO_NOTHING)
    indicia_publisher = models.ForeignKey(GcdIndiciaPublisher,
        models.DO_NOTHING, blank=True, null=True)
    indicia_pub_not_printed = models.IntegerField()
    brand = models.ForeignKey(GcdBrand, models.DO_NOTHING, blank=True,
        null=True)
    no_brand = models.IntegerField()
    publication_date = models.CharField(max_length=255)
    key_date = models.CharField(max_length=10)
    sort_code = models.IntegerField()
    price = models.CharField(max_length=255)
    page_count = models.DecimalField(max_digits=10, decimal_places=3,
        blank=True, null=True)
    page_count_uncertain = models.IntegerField()
    indicia_frequency = models.CharField(max_length=255)
    no_indicia_frequency = models.IntegerField()
    editing = models.TextField()
    no_editing = models.IntegerField()
    notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    is_indexed = models.IntegerField()
    isbn = models.CharField(max_length=32)
    valid_isbn = models.CharField(max_length=13)
    no_isbn = models.IntegerField()
    variant_of = models.ForeignKey('self', models.DO_NOTHING, blank=True,
        null=True)
    variant_name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=38)
    no_barcode = models.IntegerField()
    title = models.CharField(max_length=255)
    no_title = models.IntegerField()
    on_sale_date = models.CharField(max_length=10)
    on_sale_date_uncertain = models.IntegerField()
    rating = models.CharField(max_length=255)
    no_rating = models.IntegerField()
    volume_not_printed = models.IntegerField()
    no_indicia_printer = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_issue'
        unique_together = (('series', 'sort_code'),)


class GcdIssueCredit(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    is_credited = models.IntegerField()
    uncertain = models.IntegerField()
    credited_as = models.CharField(max_length=255)
    credit_name = models.CharField(max_length=255)
    creator = models.ForeignKey(GcdCreatorNameDetail, models.DO_NOTHING)
    credit_type = models.ForeignKey(GcdCreditType, models.DO_NOTHING)
    issue = models.ForeignKey(GcdIssue, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_issue_credit'


class GcdIssueIndiciaPrinter(models.Model):
    issue = models.ForeignKey(GcdIssue, models.DO_NOTHING)
    indiciaprinter = models.ForeignKey(GcdIndiciaPrinter, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_issue_indicia_printer'
        unique_together = (('issue', 'indiciaprinter'),)


class GcdIssueReprint(models.Model):
    origin_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING,
        related_name='%(class)s_origin_issue')
    target_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING,
        related_name='%(class)s_target_issue')
    notes = models.TextField()
    reserved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_issue_reprint'


class GcdMembershipType(models.Model):
    type = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'gcd_membership_type'


class GcdNameType(models.Model):
    description = models.TextField()
    type = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'gcd_name_type'


class GcdNonComicWorkRole(models.Model):
    role_name = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'gcd_non_comic_work_role'


class GcdNonComicWorkType(models.Model):
    type = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'gcd_non_comic_work_type'


class GcdNonComicWorkYear(models.Model):
    work_year = models.PositiveSmallIntegerField(blank=True, null=True)
    work_year_uncertain = models.IntegerField()
    non_comic_work = models.ForeignKey(GcdCreatorNonComicWork,
        models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_non_comic_work_year'


class GcdPrinter(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    name = models.CharField(max_length=255)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended_uncertain = models.IntegerField()
    notes = models.TextField()
    url = models.CharField(max_length=255)
    indicia_printer_count = models.IntegerField()
    issue_count = models.IntegerField()
    country = models.ForeignKey('StddataCountry', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_printer'


class GcdPublisher(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey('StddataCountry', models.DO_NOTHING)
    year_began = models.IntegerField(blank=True, null=True)
    year_ended = models.IntegerField(blank=True, null=True)
    notes = models.TextField()
    url = models.CharField(max_length=255)
    brand_count = models.IntegerField()
    indicia_publisher_count = models.IntegerField()
    series_count = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    issue_count = models.IntegerField()
    deleted = models.IntegerField()
    year_began_uncertain = models.IntegerField()
    year_ended_uncertain = models.IntegerField()
    year_overall_began = models.IntegerField(blank=True, null=True)
    year_overall_began_uncertain = models.IntegerField()
    year_overall_ended = models.IntegerField(blank=True, null=True)
    year_overall_ended_uncertain = models.IntegerField()

    def natural_key(self):
        return (self.pk, self.name, self.year_began,
        self.year_ended,) + self.country.natural_key()

    class Meta:
        managed = False
        db_table = 'gcd_publisher'


class GcdReceivedAward(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    object_id = models.PositiveIntegerField(blank=True, null=True)
    award_name = models.CharField(max_length=255)
    no_award_name = models.IntegerField()
    award_year = models.PositiveSmallIntegerField(blank=True, null=True)
    award_year_uncertain = models.IntegerField()
    notes = models.TextField()
    award = models.ForeignKey(GcdAward, models.DO_NOTHING, blank=True,
        null=True)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING,
        blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gcd_received_award'


class GcdRelationType(models.Model):
    type = models.CharField(max_length=50)
    reverse_type = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'gcd_relation_type'


class GcdReprint(models.Model):
    origin = models.ForeignKey('GcdStory', models.DO_NOTHING,
        related_name='%(class)s_origin')
    target = models.ForeignKey('GcdStory', models.DO_NOTHING,
        related_name='%(class)s_target')
    notes = models.TextField()
    reserved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_reprint'


class GcdReprintFromIssue(models.Model):
    origin_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING,
        related_name='%(class)s_origin')
    target = models.ForeignKey('GcdStory', models.DO_NOTHING,
        related_name='%(class)s_target')
    notes = models.TextField()
    reserved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_reprint_from_issue'


class GcdReprintToIssue(models.Model):
    origin = models.ForeignKey('GcdStory', models.DO_NOTHING)
    target_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING)
    notes = models.TextField()
    reserved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_reprint_to_issue'


class GcdSchool(models.Model):
    school_name = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'gcd_school'


class GcdSeries(models.Model):
    name = models.CharField(max_length=255)
    sort_name = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    year_began = models.IntegerField()
    year_began_uncertain = models.IntegerField()
    year_ended = models.IntegerField(blank=True, null=True)
    year_ended_uncertain = models.IntegerField()
    publication_dates = models.CharField(max_length=255)
    first_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_first_issue')
    last_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_last_issue')
    is_current = models.IntegerField()
    publisher = models.ForeignKey(GcdPublisher, models.DO_NOTHING)
    country = models.ForeignKey('StddataCountry', models.DO_NOTHING)
    language = models.ForeignKey('StddataLanguage', models.DO_NOTHING)
    tracking_notes = models.TextField()
    notes = models.TextField()
    has_gallery = models.IntegerField()
    issue_count = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    has_indicia_frequency = models.IntegerField()
    has_isbn = models.IntegerField()
    has_barcode = models.IntegerField()
    has_issue_title = models.IntegerField()
    has_volume = models.IntegerField()
    is_comics_publication = models.IntegerField()
    color = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)
    paper_stock = models.CharField(max_length=255)
    binding = models.CharField(max_length=255)
    publishing_format = models.CharField(max_length=255)
    has_rating = models.IntegerField()
    publication_type = models.ForeignKey('GcdSeriesPublicationType',
        models.DO_NOTHING, blank=True, null=True)
    is_singleton = models.IntegerField()
    has_about_comics = models.IntegerField()
    has_indicia_printer = models.IntegerField()

    def __str__(self):
        return f'{self.name} {self.publication_dates}'

    class Meta:
        managed = False
        db_table = 'gcd_series'


class GcdSeriesBond(models.Model):
    origin = models.ForeignKey(GcdSeries, models.DO_NOTHING,
        related_name='%(class)s_origin')
    target = models.ForeignKey(GcdSeries, models.DO_NOTHING,
        related_name='%(class)s_target')
    origin_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_origin_issue')
    target_issue = models.ForeignKey(GcdIssue, models.DO_NOTHING, blank=True,
        null=True,
        related_name='%(class)s_target_issue')
    bond_type = models.ForeignKey('GcdSeriesBondType', models.DO_NOTHING)
    notes = models.TextField()
    reserved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gcd_series_bond'


class GcdSeriesBondType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    notes = models.TextField()

    class Meta:
        managed = False
        db_table = 'gcd_series_bond_type'


class GcdSeriesPublicationType(models.Model):
    name = models.CharField(max_length=255)
    notes = models.TextField()

    class Meta:
        managed = False
        db_table = 'gcd_series_publication_type'


class GcdStory(models.Model):
    title = models.CharField(max_length=255)
    title_inferred = models.IntegerField()
    feature = models.CharField(max_length=255)
    sequence_number = models.IntegerField()
    page_count = models.DecimalField(max_digits=10, decimal_places=3,
        blank=True, null=True)
    issue = models.ForeignKey(GcdIssue, models.DO_NOTHING)
    script = models.TextField()
    pencils = models.TextField()
    inks = models.TextField()
    colors = models.TextField()
    letters = models.TextField()
    editing = models.TextField()
    genre = models.CharField(max_length=255)
    characters = models.TextField()
    synopsis = models.TextField()
    reprint_notes = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    notes = models.TextField()
    no_script = models.IntegerField()
    no_pencils = models.IntegerField()
    no_inks = models.IntegerField()
    no_colors = models.IntegerField()
    no_letters = models.IntegerField()
    no_editing = models.IntegerField()
    page_count_uncertain = models.IntegerField()
    type = models.ForeignKey('GcdStoryType', models.DO_NOTHING)
    job_number = models.CharField(max_length=25)
    deleted = models.IntegerField()
    first_line = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'gcd_story'


class GcdStoryCredit(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.IntegerField()
    is_credited = models.IntegerField()
    is_signed = models.IntegerField()
    uncertain = models.IntegerField()
    signed_as = models.CharField(max_length=255)
    credited_as = models.CharField(max_length=255)
    credit_name = models.CharField(max_length=255)
    creator = models.ForeignKey(GcdCreatorNameDetail, models.DO_NOTHING)
    credit_type = models.ForeignKey(GcdCreditType, models.DO_NOTHING)
    story = models.ForeignKey(GcdStory, models.DO_NOTHING)
    signature = models.ForeignKey(GcdCreatorSignature, models.DO_NOTHING,
        blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gcd_story_credit'


class GcdStoryFeatureLogo(models.Model):
    story = models.ForeignKey(GcdStory, models.DO_NOTHING)
    featurelogo = models.ForeignKey(GcdFeatureLogo, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_story_feature_logo'
        unique_together = (('story', 'featurelogo'),)


class GcdStoryFeatureObject(models.Model):
    story = models.ForeignKey(GcdStory, models.DO_NOTHING)
    feature = models.ForeignKey(GcdFeature, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gcd_story_feature_object'
        unique_together = (('story', 'feature'),)


class GcdStoryType(models.Model):
    name = models.CharField(unique=True, max_length=50)
    sort_code = models.IntegerField(unique=True)

    class Meta:
        managed = False
        db_table = 'gcd_story_type'


class StddataCountry(models.Model):
    code = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=255)

    def natural_key(self):
        return self.name, self.pk

    class Meta:
        managed = False
        db_table = 'stddata_country'


class StddataDate(models.Model):
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=2)
    day = models.CharField(max_length=2)
    year_uncertain = models.IntegerField()
    month_uncertain = models.IntegerField()
    day_uncertain = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'stddata_date'


class StddataLanguage(models.Model):
    code = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=255)
    native_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'stddata_language'


class StddataScript(models.Model):
    code = models.CharField(unique=True, max_length=4)
    number = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'stddata_script'
